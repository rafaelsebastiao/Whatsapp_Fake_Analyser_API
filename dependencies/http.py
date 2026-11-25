import httpx

from fastapi import FastAPI

from contextlib import asynccontextmanager


# Dicionário interno para guardar a instância do cliente
_shared = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda ao ligar a API, criando o cliente
    _shared["client"] = httpx.AsyncClient()
    yield
    # Roda ao desligar a API: Fecha o cliente
    await _shared["client"].aclose()

# Essa é a função que as suas ROTAS vão usar no Depends
def get_http_client() -> httpx.AsyncClient:
    return _shared["client"]