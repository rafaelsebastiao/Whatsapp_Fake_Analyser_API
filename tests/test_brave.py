import httpx
import pytest

from services.search import brave


pytestmark = pytest.mark.anyio

BRAVE_RESPONSE = {
    "web": {
        "results": [
            {
                "title": "Vacina <strong>não</strong> causa autismo",
                "url": "https://lupa.example/checagem",
                "description": "Estudos &amp; especialistas <strong>descartam</strong> relação.",
                "age": "2 days ago",
            },
            {"title": "Sem data", "url": "https://g1.example/fato", "page_age": "2026-11-20T10:00:00"},
            {"title": "Sem url"},
        ]
    }
}


def fake_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_busca_envia_parametros_e_chave():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=BRAVE_RESPONSE)

    async with fake_client(handler) as client:
        await brave.search_web("vacina autismo", client)

    request = requests[0]
    assert str(request.url).startswith(brave.BRAVE_WEB_SEARCH_URL)
    assert request.url.params["q"] == "vacina autismo"
    assert request.url.params["country"] == "BR"
    assert request.url.params["search_lang"] == "pt-br"
    assert request.headers["X-Subscription-Token"] == "test-brave-key"


async def test_busca_limpa_html_e_ignora_resultados_sem_url():
    async with fake_client(lambda request: httpx.Response(200, json=BRAVE_RESPONSE)) as client:
        results = await brave.search_web("vacina", client)

    assert results == [
        brave.SearchResult(
            title="Vacina não causa autismo",
            url="https://lupa.example/checagem",
            description="Estudos & especialistas descartam relação.",
            age="2 days ago",
        ),
        brave.SearchResult(
            title="Sem data", url="https://g1.example/fato", description="", age="2026-11-20T10:00:00",
        ),
    ]


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_erro_http_retorna_lista_vazia(status):
    async with fake_client(lambda request: httpx.Response(status)) as client:
        assert await brave.search_web("vacina", client) == []


async def test_timeout_retorna_lista_vazia():
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    async with fake_client(handler) as client:
        assert await brave.search_web("vacina", client) == []


@pytest.mark.parametrize("payload", [{}, {"web": {}}, {"web": {"results": []}}])
async def test_sem_resultados_retorna_lista_vazia(payload):
    async with fake_client(lambda request: httpx.Response(200, json=payload)) as client:
        assert await brave.search_web("vacina", client) == []


async def test_consulta_vazia_nao_chama_a_api():
    def handler(request):
        raise AssertionError("não deveria chamar a Brave")

    async with fake_client(handler) as client:
        assert await brave.search_web("   ", client) == []


async def test_consulta_longa_e_cortada_nos_limites_da_brave():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=BRAVE_RESPONSE)

    async with fake_client(handler) as client:
        await brave.search_web("palavra " * 200, client)

    query = requests[0].url.params["q"]
    assert len(query.split()) <= brave.MAX_QUERY_WORDS
    assert len(query) <= brave.MAX_QUERY_CHARS


def test_limit_query_respeita_400_caracteres():
    query = brave.limit_query(" ".join(["a" * 30] * 20))

    assert len(query) <= brave.MAX_QUERY_CHARS
    assert all(word == "a" * 30 for word in query.split())


def test_fallback_remove_links_e_emojis_e_pega_o_comeco():
    notice = "🚨 URGENTE!!! https://site.example/x " + " ".join(f"p{i}" for i in range(100))

    query = brave.fallback_query(notice)

    assert "🚨" not in query
    assert "https://" not in query
    assert query.startswith("URGENTE")
    assert len(query.split()) == brave.FALLBACK_QUERY_WORDS


def test_fallback_de_mensagem_so_com_link_usa_o_link():
    assert brave.fallback_query("https://site.example/noticia") == "https://site.example/noticia"
