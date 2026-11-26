import html
import logging
import re
from dataclasses import dataclass

from httpx import AsyncClient

from settings.settings import Settings

logger = logging.getLogger(__name__)

BRAVE_WEB_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

brave_api_key = Settings().BRAVE_SEARCH_API_KEY

# Limites da Brave para o parâmetro q: 400 caracteres e 50 palavras
MAX_QUERY_CHARS = 400
MAX_QUERY_WORDS = 50

# Palavras usadas na consulta de reserva (quando o Gemini não gera a consulta)
FALLBACK_QUERY_WORDS = 40

RESULTS_COUNT = 8

# Em segundos: a busca não pode segurar a fila de mensagens do usuário
SEARCH_TIMEOUT = 10

TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    description: str
    age: str | None = None


# Devolve lista vazia em qualquer falha: a análise segue só com o Gemini
async def search_web(query: str, client: AsyncClient) -> list[SearchResult]:
    query = limit_query(query)
    if not query:
        return []

    try:
        response = await client.get(
            BRAVE_WEB_SEARCH_URL,
            params={
                "q": query,
                "country": "BR",
                "search_lang": "pt-br",
                "ui_lang": "pt-BR",
                "count": RESULTS_COUNT,
                "safesearch": "moderate",
            },
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": brave_api_key,
            },
            timeout=SEARCH_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

    except Exception:
        logger.exception("Falha ao buscar na Brave Search")
        return []

    results = parse_results(data)
    if not results:
        logger.warning("Brave Search não retornou resultados para a consulta: %s", query)

    return results


def parse_results(data: dict) -> list[SearchResult]:
    items = (data.get("web") or {}).get("results") or []
    results = []

    for item in items:
        url = item.get("url")
        title = clean_text(item.get("title"))
        if not url or not title:
            continue

        results.append(SearchResult(
            title=title,
            url=url,
            description=clean_text(item.get("description")),
            # "age" é legível ("2 days ago", "20 de nov. de 2026"); "page_age" é ISO
            age=item.get("age") or item.get("page_age"),
        ))

    return results


# A Brave devolve trechos com <strong> e entidades HTML
def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return html.unescape(TAG_RE.sub("", value)).strip()


def limit_query(query: str, max_words: int = MAX_QUERY_WORDS) -> str:
    words = query.split()[:max_words]
    limited = " ".join(words)

    if len(limited) > MAX_QUERY_CHARS:
        # Corta na última palavra inteira que cabe
        limited = limited[:MAX_QUERY_CHARS].rsplit(" ", 1)[0]

    return limited


# Consulta de reserva: começo da notícia, sem links e sem símbolos/emojis
def fallback_query(notice: str) -> str:
    without_urls = re.sub(r"https?://\S+", " ", notice)
    words = re.sub(r"[^\w\s\-.,%$]", " ", without_urls).split()

    query = limit_query(" ".join(words), max_words=FALLBACK_QUERY_WORDS)

    # Mensagem só com um link: busca o próprio link
    return query or limit_query(notice)
