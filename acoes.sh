#!/bin/bash
set -e
# Define cores para o output (opcional, mas ajuda a ler)
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}===> Iniciando Deploy...${NC}"

# 1. Puxa as últimas alterações do Git
# (Assumindo que você configurou a Chave SSH como vimos antes)
echo -e "${GREEN}===> Atualizando código com Git Pull...${NC}"
cd /opt/docker/acoes/

git pull proavante main

# 2. Reconstrói e sobe os containers
# O flag --build garante que o Docker refaça a imagem se o código mudou
echo -e "${GREEN}===> Reconstruindo containers com Docker Compose...${NC}"
docker-compose down
docker-compose up -d --build acoes-app

# 3. Limpeza de imagens antigas
# Remove imagens que ficaram sem nome (dangling) para não encher o disco
echo -e "${GREEN}===> Limpando imagens antigas (prune)...${NC}"
docker image prune -f

echo -e "${GREEN}===> Deploy finalizado com sucesso!${NC}"


