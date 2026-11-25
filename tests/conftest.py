import os

import pytest


# Valores falsos: o Settings() e o cliente do Gemini são criados no import dos módulos.
# Variáveis de ambiente têm prioridade sobre o .env, então nenhum teste usa as chaves reais.
os.environ["OWN_API_URL"] = "http://fake-analyser-api.test:8000"
os.environ["EVOLUTION_API_URL"] = "http://evolution-api.test:8080"
os.environ["EVOLUTION_AUTHENTICATION_API_KEY"] = "test-evolution-key"
os.environ["CHATBOT_INSTANCE_NAME"] = "test-instance"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"


# Testes async rodam com o plugin do anyio (já instalado com o FastAPI), só no asyncio
@pytest.fixture
def anyio_backend():
    return "asyncio"
