FROM python:3.11-slim

# Variáveis de ambiente essenciais (podem ser sobrescritas pelo Railway)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Defina o WORKDIR dentro do container
    WORKDIR=/app

# Instala git (necessário para GitPython) e limpa cache
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia apenas o requirements.txt primeiro para aproveitar o cache do Docker
COPY requirements.txt ./

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do backend
COPY . .

# Expõe a porta que o Uvicorn vai usar (Railway injetará a $PORT correta)
EXPOSE 8000

# Comando para iniciar a aplicação usando a variável $PORT injetada pelo Railway
# Usamos sh -c para permitir a expansão da variável de ambiente $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1"]
# Nota: --workers 1 é geralmente recomendado para começar em ambientes gerenciados como Railway.
# Ajuste se necessário após testes de carga. Use Gunicorn se precisar de mais controle.
