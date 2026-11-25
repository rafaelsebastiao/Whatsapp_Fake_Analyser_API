import json
from functools import cache
from pathlib import Path

from google import genai
from google.genai import types

from settings.settings import Settings

base_path = Path().cwd()
prompt_path = base_path / "prompts" / "prompt.json"

# Timeout em milissegundos: evita que a drenagem do usuário fique presa se a IA travar
client = genai.Client(
    api_key=Settings().GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=30_000),
)


async def text_analisys(notice: str) -> str:
    prompt = get_prompt_text()

    try:
        response = await client.aio.models.generate_content(
            model='gemini-3.6-flash',
            contents=notice,
            config=types.GenerateContentConfig(system_instruction=prompt),

        )

    except Exception as e:
        return f'Não foi possível analisar agora, tente novamente em instantes. {e}'

    return response.text


@cache
def get_prompt_text() -> str:
    # Lido uma vez só; o @cache evita abrir o arquivo a cada mensagem
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return json.load(file)["text"]