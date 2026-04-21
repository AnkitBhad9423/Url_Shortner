# app/schemas.py

from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    """What the client sends to POST /api/shorten"""
    long_url: HttpUrl          # Pydantic validates this is a real URL automatically


class ShortenResponse(BaseModel):
    """What we send back"""
    short_code: str
    short_url:  str
    long_url:   str