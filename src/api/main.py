from fastapi import FastAPI
from src.api.routes.chat import router as chat_router

app = FastAPI(title="Enterprise AI Agent API")

app.include_router(chat_router, prefix="/api/v1")