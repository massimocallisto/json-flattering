#!/bin/sh

docker kill flat
docker rm flat

docker run -d \
    --name=flat \
    -v config.json:/app/config.json \
    massimocallisto/json-flattering:1.0.0

docker logs -f flat
