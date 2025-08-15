import base64
import json
from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.Random import get_random_bytes

def pad(data: bytes, block_size: int) -> bytes:
    padding_len = block_size - len(data) % block_size
    return data + bytes([padding_len]) * padding_len

def unpad(data: bytes, block_size: int) -> bytes:
    padding_len = data[-1]
    if padding_len > block_size:
        raise ValueError("Invalid padding length")
    return data[:-padding_len]

def encrypt(payload: dict, devicekey: str) -> dict:
    key = MD5.new(devicekey.encode("utf-8")).digest()
    iv = get_random_bytes(16)
    plaintext = json.dumps(payload["data"]).encode("utf-8")
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    padded = pad(plaintext, AES.block_size)
    ciphertext = cipher.encrypt(padded)
    payload.update({
        "encrypt": True,
        "data": base64.b64encode(ciphertext).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8")
    })
    return payload

def decrypt(payload: dict, devicekey: str) -> dict:
    key = MD5.new(devicekey.encode("utf-8")).digest()
    cipher = AES.new(key, AES.MODE_CBC, iv=base64.b64decode(payload["iv"]))
    ciphertext = base64.b64decode(payload["data"])
    padded = cipher.decrypt(ciphertext)
    data = unpad(padded, AES.block_size)
    if data and data.startswith(b'{"rf'):
        data = data.replace(b'"="', b'":"')
    data = data.rstrip(b"\x02").decode('utf-8') or '{}'
    payload["data"] = json.loads(data)
    return payload