#!/bin/sh

docker kill flat
docker rm flat

docker run -d \
    --name=flat \
    --restart=always \
    -v ./config.json:/config.json \
    massimocallisto/json-flattering:1.0.0

docker logs -f flat
