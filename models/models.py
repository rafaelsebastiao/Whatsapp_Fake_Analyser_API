import uuid

from datetime import datetime

from sqlalchemy import Uuid, String, func
from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()


@table_registry.mapped_as_dataclass
class UserModel:
    __tablename__='users'
    
    
    id:Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, init=False)


    telephoneNumber: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100))

    lastMessage: Mapped[str] = mapped_column(String)

    timeStampMessage: Mapped[str] = mapped_column(String)



    created_at:Mapped[datetime] = mapped_column(init=False, server_default=func.now())
