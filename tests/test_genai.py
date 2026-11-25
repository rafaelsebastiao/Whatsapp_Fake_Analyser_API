from types import SimpleNamespace

import pytest

from services.ai import genai


pytestmark = pytest.mark.anyio


class FakeModels:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def fake_gemini(monkeypatch, **kwargs) -> FakeModels:
    models = FakeModels(**kwargs)
    monkeypatch.setattr(genai, "client", SimpleNamespace(aio=SimpleNamespace(models=models)))
    return models


async def test_retorna_o_texto_da_analise(monkeypatch):
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text="É falsa."))

    assert await genai.text_analisys("notícia") == "É falsa."
    assert models.calls[0]["contents"] == "notícia"


async def test_falha_retorna_none_sem_vazar_o_erro(monkeypatch):
    fake_gemini(monkeypatch, error=RuntimeError("chave inválida"))

    assert await genai.text_analisys("notícia") is None


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_resposta_sem_texto_retorna_none(monkeypatch, text):
    fake_gemini(monkeypatch, result=SimpleNamespace(text=text))

    assert await genai.text_analisys("notícia") is None
