FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=2.2,<3"

# Instala as dependências primeiro (aproveita o cache de camadas do Docker)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-ansi

# Código do projeto (o .env fica de fora, ver .dockerignore)
COPY . .

EXPOSE 8000

# Roda a partir da raiz (/app) para os imports "dependencies", "routes", "services" e "settings" funcionarem
CMD ["uvicorn", "fake_analyser_api.main:app", "--host", "0.0.0.0", "--port", "8000"]