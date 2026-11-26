import pytest

from services.analysis import news
from services.search.brave import SearchResult


pytestmark = pytest.mark.anyio

RESULTS = [SearchResult(title=f"T{i}", url=f"https://fonte{i}.example", description="") for i in range(1, 7)]


class Pipeline:
    def __init__(self, monkeypatch, query="consulta gerada", results=RESULTS, analysis="*Veredito:* ❌ Falsa [2]"):
        self.query = query
        self.results = results
        self.analysis = analysis
        self.calls: list[tuple] = []

        monkeypatch.setattr(news, "search_query", self.search_query)
        monkeypatch.setattr(news, "search_web", self.search_web)
        monkeypatch.setattr(news, "text_analisys", self.text_analisys)

    async def search_query(self, notice):
        self.calls.append(("search_query", notice))
        return self.query

    async def search_web(self, query, client):
        self.calls.append(("search_web", query))
        return self.results

    async def text_analisys(self, notice, results):
        self.calls.append(("text_analisys", notice, results))
        return self.analysis


async def test_fluxo_consulta_busca_e_analise_em_ordem(monkeypatch):
    pipeline = Pipeline(monkeypatch)

    await news.analyse_news("Notícia", client=None)

    assert pipeline.calls == [
        ("search_query", "Notícia"),
        ("search_web", "consulta gerada"),
        ("text_analisys", "Notícia", RESULTS),
    ]


async def test_sem_consulta_do_gemini_usa_o_comeco_da_noticia(monkeypatch):
    pipeline = Pipeline(monkeypatch, query=None)

    await news.analyse_news("🚨 Vacina causa autismo", client=None)

    assert pipeline.calls[1] == ("search_web", "Vacina causa autismo")


async def test_falha_da_busca_ainda_analisa_sem_fontes(monkeypatch):
    pipeline = Pipeline(monkeypatch, results=[], analysis="*Veredito:* ❓ Não foi possível confirmar")

    result = await news.analyse_news("Notícia", client=None)

    assert pipeline.calls[2] == ("text_analisys", "Notícia", [])
    assert result == "*Veredito:* ❓ Não foi possível confirmar"


async def test_falha_da_analise_retorna_none(monkeypatch):
    Pipeline(monkeypatch, analysis=None)

    assert await news.analyse_news("Notícia", client=None) is None


async def test_anexa_os_links_citados(monkeypatch):
    Pipeline(monkeypatch, analysis="*Justificativa:* segundo [3] e [1][3].")

    result = await news.analyse_news("Notícia", client=None)

    assert result.endswith("*Fontes:*\n[3] https://fonte3.example\n[1] https://fonte1.example")


def test_sem_citacao_lista_os_3_primeiros():
    result = news.append_sources("Análise", RESULTS)

    assert result == (
        "Análise\n\n*Fontes:*\n"
        "[1] https://fonte1.example\n[2] https://fonte2.example\n[3] https://fonte3.example"
    )


def test_ignora_citacoes_inexistentes_e_limita_a_5():
    result = news.append_sources("[9] [6] [5] [4] [3] [2] [1]", RESULTS)

    assert "fonte9" not in result
    assert result.count("https://") == news.MAX_SOURCES


def test_sem_resultados_nao_anexa_fontes():
    assert news.append_sources("Análise", []) == "Análise"
