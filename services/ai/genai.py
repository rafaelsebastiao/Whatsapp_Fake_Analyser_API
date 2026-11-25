import json
import logging
from functools import cache
from pathlib import Path

from google import genai
from google.genai import types

from settings.settings import Settings

logger = logging.getLogger(__name__)

base_path = Path().cwd()
prompt_path = base_path / "prompts" / "prompt.json"

# Timeout em milissegundos: evita que a drenagem do usuário fique presa se a IA travar
client = genai.Client(
    api_key=Settings().GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=30_000),
)


# Retorna o texto da análise, ou None se a IA falhar ou não devolver texto
async def text_analisys(notice: str) -> str | None:
    prompt = get_prompt_text()

    try:
        response = await client.aio.models.generate_content(
            model='gemini-3.6-flash',
            contents=notice,
            config=types.GenerateContentConfig(system_instruction=prompt),

        )

    except Exception:
        # O erro fica só no log; o usuário recebe uma mensagem padrão
        logger.exception("Falha ao analisar a notícia no Gemini")
        return None

    # response.text vem None quando a resposta é bloqueada ou vazia
    if not response.text or not response.text.strip():
        logger.warning("Gemini não retornou texto na análise")
        return None

    return response.text


@cache
def get_prompt_text() -> str:
    # Lido uma vez só; o @cache evita abrir o arquivo a cada mensagem
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return json.load(file)["text"]
