#!/bin/bash

# --- Configurazione ---
VERSION="1.1.0-dipme"
IMAGE_NAME="massimocallisto/json-flattering"
TAG_FULL="$IMAGE_NAME:$VERSION"

# 1. Comando di Build
echo "Building $TAG_FULL..."
docker build --no-cache -t "$TAG_FULL" .

# Controllo esito build (Corretto il typo 'Erro')
if [ $? -ne 0 ]; then
    echo "Error building docker image."
    exit 1
fi

# 2. Richiesta conferma per il Push
# Aggiunto spazio dopo (y/n) per leggibilità
read -p "Push on Docker Hub? (y/n): " confirm

# Utilizzo di case per gestire meglio le varianti di 'yes'
case "$confirm" in
    [yY]|[yY][eE][sS])
        echo "Pushing $TAG_FULL..."
        docker push "$TAG_FULL"
        ;;
    *)
        echo "Push skipped."
        ;;
esac
