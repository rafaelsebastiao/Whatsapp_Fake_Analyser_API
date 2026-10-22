from google import genai

from settings.settings import Settings

gemini_api_key = Settings().GEMINI_API_KEY

client = genai.Client(gemini_api_key)

def text_analisys(notice: str):

    response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=f'Analise a nóticia que o usuário informou e retorne se é fake news ou se é verdadeira: {notice}',
    )

    return response.text