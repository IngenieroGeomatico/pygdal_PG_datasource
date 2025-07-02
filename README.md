# pygdal_PG_datasource

Documentación en desarrollo


export PYTHONPATH=$(pwd)

export PYGEOAPI_OPENAPI=example-openapi.yml

export PYGEOAPI_CONFIG="pygeoapi/pygeoapi_complementos/test/pygeoapi-config_OGR_DataProvider.yml"

pygeoapi openapi generate $PYGEOAPI_CONFIG --output-file $PYGEOAPI_OPENAPI

pygeoapi serve --django

