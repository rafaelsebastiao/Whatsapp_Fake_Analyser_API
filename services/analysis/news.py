import logging
import re

from httpx import AsyncClient

from services.ai.genai import search_query, text_analisys
from services.search.brave import SearchResult, fallback_query, search_web

logger = logging.getLogger(__name__)

# Quantos links listar quando o Gemini não citar nenhuma fonte com [n]
DEFAULT_SOURCES = 3
MAX_SOURCES = 5

CITATION_RE = re.compile(r"\[(\d{1,2})\]")


# Fluxo da análise: consulta curta (Gemini) → busca (Brave) → veredito (Gemini) + links.
# Retorna None só quando a análise em si falha; a falha da busca não impede a resposta.
async def analyse_news(notice: str, client: AsyncClient) -> str | None:
    query = await search_query(notice) or fallback_query(notice)
    logger.info("Consulta de busca: %s", query)

    results = await search_web(query, client)

    analysis = await text_analisys(notice, results)
    if analysis is None:
        return None

    return append_sources(analysis, results)


# Os links vêm dos resultados reais da Brave, nunca do texto do modelo
def append_sources(analysis: str, results: list[SearchResult]) -> str:
    if not results:
        return analysis

    cited = cited_numbers(analysis, len(results))
    numbers = cited[:MAX_SOURCES] or list(range(1, min(DEFAULT_SOURCES, len(results)) + 1))

    lines = [f"[{number}] {results[number - 1].url}" for number in numbers]
    return f"{analysis.rstrip()}\n\n*Fontes:*\n" + "\n".join(lines)


# Números citados no texto, na ordem em que aparecem, sem repetir e só os que existem
def cited_numbers(analysis: str, total: int) -> list[int]:
    numbers: list[int] = []
    for match in CITATION_RE.finditer(analysis):
        number = int(match.group(1))
        if 1 <= number <= total and number not in numbers:
            numbers.append(number)
    return numbers
