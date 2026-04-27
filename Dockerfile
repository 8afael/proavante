# Usar uma imagem Python estável
FROM python:3.11-slim

# Definir variáveis de ambiente para evitar arquivos .pyc e buffer de log
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Definir diretório de trabalho
WORKDIR /proavante/app

# Instalar dependências do sistema necessárias para o psycopg2 (Postgres)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas o arquivo de requisitos primeiro (melhora o cache do Docker)
COPY requirements.txt .

# Instalar dependências do Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY . .

# Expor a porta que a aplicação vai rodar
EXPOSE 8080

# Comando para iniciar a aplicação usando Gunicorn com workers Uvicorn
# Ajustado para escutar em 0.0.0.0 e na porta 8080
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
