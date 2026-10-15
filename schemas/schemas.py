from pydantic import BaseModel

class UserSchema(BaseModel):
    telephoneNumber:str | None     
    name:str | None
    lastMessage:str 
    timeStampMessage:str 