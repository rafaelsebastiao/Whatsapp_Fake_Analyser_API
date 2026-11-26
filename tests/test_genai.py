from types import SimpleNamespace

import pytest

from services.ai import genai
from services.search.brave import SearchResult


pytestmark = pytest.mark.anyio

RESULTS = [
    SearchResult(title="Checagem: vacina não causa autismo", url="https://lupa.example/1",
                 description="Estudos descartam relação.", age="20 de nov. de 2026"),
    SearchResult(title="Ministério da Saúde", url="https://gov.example/2", description=""),
]


class FakeModels:
    # by_model: respostas por modelo ({modelo: resultado ou exceção}); os demais usam result/error
    def __init__(self, result=None, error=None, by_model=None):
        self.result = result
        self.error = error
        self.by_model = by_model or {}
        self.calls = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.by_model.get(kwargs["model"], self.error or self.result)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def fake_gemini(monkeypatch, **kwargs) -> FakeModels:
    models = FakeModels(**kwargs)
    monkeypatch.setattr(genai, "client", SimpleNamespace(aio=SimpleNamespace(models=models)))
    return models


# ---------- text_analisys ----------

async def test_retorna_o_texto_da_analise(monkeypatch):
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text="É falsa."))

    assert await genai.text_analisys("notícia", RESULTS) == "É falsa."
    assert "<noticia>\nnotícia\n</noticia>" in models.calls[0]["contents"]


async def test_conteudo_inclui_data_de_hoje_e_resultados_numerados(monkeypatch):
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text="ok"))

    await genai.text_analisys("Vacina causa autismo", RESULTS)
    contents = models.calls[0]["contents"]

    assert contents.startswith("Data de hoje: ")
    assert "[1] Checagem: vacina não causa autismo" in contents
    assert "Data: 20 de nov. de 2026" in contents
    assert "Trecho: Estudos descartam relação." in contents
    assert "Fonte: https://lupa.example/1" in contents
    assert "[2] Ministério da Saúde" in contents


async def test_sem_resultados_avisa_o_modelo(monkeypatch):
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text="ok"))

    await genai.text_analisys("notícia", [])

    assert "Nenhum resultado disponível" in models.calls[0]["contents"]


async def test_falha_retorna_none_sem_vazar_o_erro(monkeypatch):
    fake_gemini(monkeypatch, error=RuntimeError("chave inválida"))

    assert await genai.text_analisys("notícia", RESULTS) is None


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_resposta_sem_texto_retorna_none(monkeypatch, text):
    fake_gemini(monkeypatch, result=SimpleNamespace(text=text))

    assert await genai.text_analisys("notícia", RESULTS) is None


async def test_modelo_sobrecarregado_passa_para_o_proximo(monkeypatch):
    monkeypatch.setattr(genai, "ANALYSIS_MODELS", ["sobrecarregado", "reserva"])
    models = fake_gemini(monkeypatch, by_model={
        "sobrecarregado": RuntimeError("503 UNAVAILABLE"),
        "reserva": SimpleNamespace(text="*Veredito:* ❌ Falsa"),
    })

    assert await genai.text_analisys("notícia", RESULTS) == "*Veredito:* ❌ Falsa"
    assert [call["model"] for call in models.calls] == ["sobrecarregado", "reserva"]


async def test_resposta_vazia_tambem_passa_para_o_proximo(monkeypatch):
    monkeypatch.setattr(genai, "ANALYSIS_MODELS", ["vazio", "reserva"])
    fake_gemini(monkeypatch, by_model={
        "vazio": SimpleNamespace(text=None),
        "reserva": SimpleNamespace(text="ok"),
    })

    assert await genai.text_analisys("notícia", RESULTS) == "ok"


async def test_primeiro_modelo_ok_nao_chama_os_outros(monkeypatch):
    monkeypatch.setattr(genai, "ANALYSIS_MODELS", ["principal", "reserva"])
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text="ok"))

    await genai.text_analisys("notícia", RESULTS)

    assert [call["model"] for call in models.calls] == ["principal"]


async def test_todos_os_modelos_falham_retorna_none(monkeypatch):
    monkeypatch.setattr(genai, "ANALYSIS_MODELS", ["a", "b", "c"])
    models = fake_gemini(monkeypatch, error=RuntimeError("503"))

    assert await genai.text_analisys("notícia", RESULTS) is None
    assert len(models.calls) == 3


async def test_cada_chamada_tem_timeout_proprio(monkeypatch):
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text="ok"))

    await genai.text_analisys("notícia", RESULTS)
    await genai.search_query("notícia")

    assert models.calls[0]["config"].http_options.timeout == genai.ANALYSIS_TIMEOUT_MS
    assert models.calls[1]["config"].http_options.timeout == genai.QUERY_TIMEOUT_MS


# ---------- search_query ----------

async def test_consulta_usa_primeira_linha_sem_aspas(monkeypatch):
    models = fake_gemini(monkeypatch, result=SimpleNamespace(text='"vacina autismo Anvisa"\nexplicação'))

    assert await genai.search_query("URGENTE!!! vacina causa autismo") == "vacina autismo Anvisa"
    assert models.calls[0]["contents"] == "URGENTE!!! vacina causa autismo"


async def test_consulta_falha_retorna_none(monkeypatch):
    fake_gemini(monkeypatch, error=RuntimeError("timeout"))

    assert await genai.search_query("notícia") is None


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_consulta_vazia_retorna_none(monkeypatch, text):
    fake_gemini(monkeypatch, result=SimpleNamespace(text=text))

    assert await genai.search_query("notícia") is None


def test_prompts_existem():
    assert genai.get_prompt_text("prompt")
    assert genai.get_prompt_text("search_query")
