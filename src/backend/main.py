from fastapi import FastAPI
from backend.api import text_to_text

app = FastAPI()

app.include_router(text_to_text.router, prefix="/api")