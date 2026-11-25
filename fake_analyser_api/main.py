from fastapi import FastAPI

from dependencies.http import lifespan

from routes.instances import router as instances_router

from routes.messages import router as messages_router


# Passar o lifespan para o fastapi
app = FastAPI(lifespan=lifespan)

app.include_router(instances_router)
app.include_router(messages_router)

