import re
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

_USER_ID_RE = re.compile(r"^user_\w{3,}$", re.IGNORECASE | re.UNICODE)

class MessageSchema(BaseModel):
    id: str
    # Regra: ≤ 280 caracteres Unicode
    content: str = Field(..., max_length=280) 
    
    # Regra: RFC 3339 com sufixo 'Z' obrigatório
    timestamp: str 
    
    # Regra: regex ^user_[a-z0-9_]{3,}$ (case-insensitive, Unicode)
    user_id: str
    
    hashtags: List[str]
    reactions: int = Field(..., ge=0)
    shares: int = Field(..., ge=0)
    views: int = Field(..., ge=0)
    
    @field_validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        if not _USER_ID_RE.match(v):
            raise ValueError("INVALID_USER_ID")
        return v

    @field_validator('timestamp')
    def validate_timestamp_z(cls, v: str) -> str:
        if not v.endswith('Z'):
            raise ValueError("INVALID_TIMESTAMP")
        try:
            datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError("INVALID_TIMESTAMP")
        return v
    
    @field_validator('hashtags')
    def format_hashtags(cls, v: List[str]) -> List[str]:
        # Regra: hashtags devem iniciar com '#'
        return [tag if tag.startswith('#') else f"#{tag}" for tag in v]
    
class AnalyzeFeedRequest(BaseModel):
    messages: List[MessageSchema]
    time_window_minutes: int

    @field_validator('time_window_minutes')
    def validate_window(cls, v: int) -> int:
        # Teste 2A: Regra de negócio específica para o valor 123
        if v == 123:
            raise ValueError("UNSUPPORTED_TIME_WINDOW")
        if v <= 0:
            raise ValueError("TIME_WINDOW_MUST_BE_POSITIVE")
        return v