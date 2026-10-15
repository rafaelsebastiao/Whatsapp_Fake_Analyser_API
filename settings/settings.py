from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    OWN_API_URL : str
    EVOLUTION_API_URL:str 
    EVOLUTION_AUTHENTICATION_API_KEY : str
    CHATBOT_INSTANCE_NAME:str
