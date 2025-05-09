from pydantic import BaseModel

class TextRequest(BaseModel):
    input_text: str

class TextResponse(BaseModel):
    output_text: str