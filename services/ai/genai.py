import json
import logging
from datetime import datetime, timedelta, timezone
from functools import cache
from pathlib import Path

from google import genai
from google.genai import types

from services.search.brave import SearchResult
from settings.settings import Settings

logger = logging.getLogger(__name__)

base_path = Path().cwd()
prompts_path = base_path / "prompts"

settings = Settings()

ANALYSIS_MODELS = [model.strip() for model in settings.GEMINI_MODELS.split(",") if model.strip()]
QUERY_MODELS = [model.strip() for model in settings.GEMINI_QUERY_MODELS.split(",") if model.strip()]

# Timeout por modelo, em milissegundos. Curto de propósito: um modelo sobrecarregado
# às vezes fica pendurado em vez de responder 503, e aí passamos para o próximo.
ANALYSIS_TIMEOUT_MS = 20_000
QUERY_TIMEOUT_MS = 8_000

# Horário de Brasília (sem horário de verão desde 2019); não depende do tzdata da imagem
BRASILIA = timezone(timedelta(hours=-3))

client = genai.Client(api_key=settings.GEMINI_API_KEY)


# Tenta cada modelo em ordem e devolve o primeiro texto não vazio, ou None se todos falharem
async def generate_with_fallback(
    models: list[str],
    contents: str,
    system_instruction: str,
    timeout_ms: int,
    task: str,
) -> str | None:
    for model in models:
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    http_options=types.HttpOptions(timeout=timeout_ms),
                ),
            )

        except Exception as error:
            # 503 (alta demanda), 429 (cota), timeout...: o próximo modelo resolve
            logger.warning("Gemini %s falhou em %s: %s", model, task, error)
            continue

        # response.text vem None quando a resposta é bloqueada ou vazia
        if response.text and response.text.strip():
            return response.text

        logger.warning("Gemini %s não retornou texto em %s", model, task)

    logger.error("Todos os modelos do Gemini falharam em %s: %s", task, ", ".join(models))
    return None


# Retorna uma consulta curta para o buscador, ou None se a IA falhar
async def search_query(notice: str) -> str | None:
    # O tamanho final é cortado em search_web (limites da Brave)
    text = await generate_with_fallback(
        QUERY_MODELS, notice, get_prompt_text("search_query"), QUERY_TIMEOUT_MS, "consulta de busca",
    )
    if text is None:
        return None

    # Só a primeira linha, sem aspas que o modelo às vezes coloca
    return text.strip().splitlines()[0].strip().strip('"\'')


# Retorna o texto da análise, ou None se a IA falhar ou não devolver texto
async def text_analisys(notice: str, search_results: list[SearchResult]) -> str | None:
    # O erro fica só no log; o usuário recebe uma mensagem padrão
    return await generate_with_fallback(
        ANALYSIS_MODELS,
        build_analysis_contents(notice, search_results),
        get_prompt_text("prompt"),
        ANALYSIS_TIMEOUT_MS,
        "análise",
    )


def build_analysis_contents(notice: str, search_results: list[SearchResult]) -> str:
    today = datetime.now(BRASILIA).strftime("%d/%m/%Y")

    if search_results:
        sources = "\n\n".join(
            format_result(number, result)
            for number, result in enumerate(search_results, start=1)
        )
    else:
        sources = (
            "Nenhum resultado disponível (a busca falhou ou não encontrou nada). "
            "Se não tiver certeza, responda que não foi possível confirmar."
        )

    return (
        f"Data de hoje: {today}\n\n"
        f"<noticia>\n{notice}\n</noticia>\n\n"
        f"<resultados_da_busca>\n{sources}\n</resultados_da_busca>"
    )


def format_result(number: int, result: SearchResult) -> str:
    lines = [f"[{number}] {result.title}"]
    if result.age:
        lines.append(f"Data: {result.age}")
    if result.description:
        lines.append(f"Trecho: {result.description}")
    lines.append(f"Fonte: {result.url}")
    return "\n".join(lines)


@cache
def get_prompt_text(name: str) -> str:
    # Lido uma vez só; o @cache evita abrir o arquivo a cada mensagem
    with open(prompts_path / f"{name}.json", 'r', encoding='utf-8') as file:
        return json.load(file)["text"]
