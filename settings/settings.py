from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    OWN_API_URL : str
    EVOLUTION_API_URL:str 
    EVOLUTION_AUTHENTICATION_API_KEY : str
    CHATBOT_INSTANCE_NAME:str
    GEMINI_API_KEY: str
    BRAVE_SEARCH_API_KEY: str

    # Modelos do Gemini em ordem de preferência, separados por vírgula.
    # Se um estiver sobrecarregado (503) ou demorar demais, tenta o próximo.
    GEMINI_MODELS: str = "gemini-3.6-flash,gemini-flash-latest,gemini-3.5-flash-lite"
    # Geração da consulta de busca: tarefa simples, começa pelo modelo mais rápido
    GEMINI_QUERY_MODELS: str = "gemini-3.5-flash-lite,gemini-flash-latest"
