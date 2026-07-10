from pydantic import BaseModel
from datetime import datetime


class ChatMessageRequest(BaseModel):
    message: str


class ChatStreamRequest(BaseModel):
    message: str


import uuid

class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]


class SuggestionsResponse(BaseModel):
    suggestions: list[str]
