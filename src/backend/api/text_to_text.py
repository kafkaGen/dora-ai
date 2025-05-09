from fastapi import APIRouter
from backend.models.schemas import TextRequest, TextResponse
from backend.services.text_processor import process_text

router = APIRouter()

@router.post("/text-to-text", response_model=TextResponse, tags=["Text"])
async def text_to_text_endpoint(request: TextRequest):
    """
    Process input text and return the transformed result.
    """
    output = process_text(request.input_text)
    return TextResponse(output_text=output)