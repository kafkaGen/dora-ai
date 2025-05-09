from fastapi import FastAPI
from backend.models.schemas import TextRequest, TextResponse

app = FastAPI()

@app.post("/api/text-to-text", response_model=TextResponse)
async def text_to_text_endpoint(request: TextRequest):
    # Simple text transformation logic (replace this with your own)
    processed_text = request.input_text.upper()
    return TextResponse(output_text=processed_text)