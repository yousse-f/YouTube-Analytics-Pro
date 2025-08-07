from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class YouTubeRequest(BaseModel):
    url: str = Field(..., description="URL del canale YouTube da analizzare")


class YouTubeScrapingResult(BaseModel):
    channel_name: str = Field(..., description="Nome del canale YouTube")
    channel_handle: str = Field(..., description="Handle del canale YouTube")
    subscribers: str = Field(..., description="Numero iscritti visibile pubblicamente")
    videos: str = Field(..., description="Numero di video visibile pubblicamente")
    description: str = Field(..., description="Descrizione del canale")
    first_10_videos: List[str] = Field(..., description="Primi 10 video trovati")

    error_message: Optional[str] = Field(
        None, description="Messaggio di errore se lo scraping fallisce"
    )
