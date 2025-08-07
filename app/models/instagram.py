# app/models/instagram.py
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class InstagramRequest(BaseModel):
    username: str = Field(
        ..., description="Username del profilo Instagram da analizzare"
    )


class ProfileAndPresence(BaseModel):
    current_followers: int = Field(..., description="Follower attuali - DATO REALE")
    total_posts: int = Field(..., description="Numero totale post - DATO REALE")
    follower_growth: Optional[float] = Field(
        None,
        description="Crescita follower percentuale - NON DISPONIBILE tramite scraping pubblico",
    )
    quality_estimate: Optional[str] = Field(
        None,
        description="Qualità stimata follower - NON DISPONIBILE tramite scraping pubblico",
    )


class FrequencyAndActivity(BaseModel):
    posting_frequency: Dict[str, str] = Field(
        ...,
        description="Frequenza di pubblicazione calcolata dai post reali degli ultimi 30 giorni",
    )
    content_statistics: Dict[str, Any] = Field(
        ...,
        description="Statistiche reali per tipo di contenuto basate sui post pubblici",
    )


class KPIAndPerformance(BaseModel):
    engagement_rate: float = Field(
        ...,
        description="Engagement rate calcolato da like e commenti reali dei post pubblici",
    )
    impressions: Optional[int] = Field(
        None, description="Impressioni totali - NON DISPONIBILE tramite API pubblica"
    )
    reach: Optional[int] = Field(
        None, description="Reach totale - NON DISPONIBILE tramite API pubblica"
    )
    avg_likes_per_post: float = Field(
        ..., description="Media like per post - DATO REALE calcolato dai post pubblici"
    )
    avg_comments_per_post: float = Field(
        ...,
        description="Media commenti per post - DATO REALE calcolato dai post pubblici",
    )
    video_views: Optional[int] = Field(
        None, description="Visualizzazioni video - NON DISPONIBILE tramite API pubblica"
    )
    reel_plays: Optional[int] = Field(
        None, description="Reel plays - NON DISPONIBILE tramite API pubblica"
    )
    view_through_rate: Optional[float] = Field(
        None, description="View-through rate - NON DISPONIBILE tramite API pubblica"
    )
    stories_impression_rate: Optional[float] = Field(
        None,
        description="Tasso di impression stories - NON DISPONIBILE tramite API pubblica",
    )
    bio_link_ctr: Optional[float] = Field(
        None, description="CTR link in bio - NON DISPONIBILE tramite API pubblica"
    )
    avg_reach_per_post: Optional[float] = Field(
        None, description="Media reach per post - NON DISPONIBILE tramite API pubblica"
    )
    avg_interactions_per_post: float = Field(
        ..., description="Media interazioni per post - DATO REALE (like + commenti)"
    )
    follower_demographics: Optional[str] = Field(
        None,
        description="Dati demografici follower - NON DISPONIBILE tramite API pubblica",
    )


class ContentAndFormat(BaseModel):
    content_types: Dict[str, Any] = Field(
        ...,
        description="Tipologie di contenuto basate sui post reali - percentuali e conteggi effettivi",
    )
    creative_analysis: Literal[
        "dinamici", "minimal", "premium", "colorati", "monocromatici"
    ] = Field(
        ...,
        description="Analisi creativa basata sulle caption e stile reali dei contenuti",
    )
    best_content: List[Dict[str, str]] = Field(
        ..., description="Top 3 contenuti migliori con link e engagement REALI"
    )


class InstagramToneOfVoice(BaseModel):
    tone: Literal[
        "ironico",
        "istituzionale",
        "educativo",
        "motivazionale",
        "casual",
        "professionale",
    ] = Field(..., description="Tone of voice analizzato dalle caption reali dei post")


class TrendsAndHashtags(BaseModel):
    active_trends: bool = Field(
        ..., description="Utilizzo trend attivi basato sull'analisi degli hashtag reali"
    )
    effective_formats: bool = Field(
        ...,
        description="Utilizzo format efficaci basato sulla varietà di contenuti reali",
    )
    hashtag_analysis: str = Field(
        ..., description="Analisi degli hashtag estratti dai post reali"
    )


class InstagramFunnelAndObjectives(BaseModel):
    profile_objective: Literal["awareness", "conversione", "fidelizzazione"] = Field(
        ..., description="Obiettivo del profilo analizzato dalla bio e caption reali"
    )
    brand_ambassadors: bool = Field(
        ...,
        description="Presenza di brand ambassador rilevata dalle caption e bio reali",
    )


class InstagramScrapingResult(BaseModel):
    username: str = Field(..., description="Username analizzato")
    scraping_date: str = Field(..., description="Data dello scraping")

    profile_presence: ProfileAndPresence = Field(
        default_factory=ProfileAndPresence, description="Profilo e presenza"
    )
    frequency_activity: FrequencyAndActivity = Field(
        default_factory=FrequencyAndActivity, description="Frequenza e attività"
    )
    kpi_performance: KPIAndPerformance = Field(
        default_factory=KPIAndPerformance, description="KPI e performance"
    )
    content_format: ContentAndFormat = Field(
        default_factory=ContentAndFormat, description="Contenuti e format"
    )
    tone_of_voice: InstagramToneOfVoice = Field(
        default_factory=InstagramToneOfVoice, description="Tone of Voice"
    )
    trends_hashtags: TrendsAndHashtags = Field(
        default_factory=TrendsAndHashtags, description="Trend e hashtag"
    )
    funnel_objectives: InstagramFunnelAndObjectives = Field(
        default_factory=InstagramFunnelAndObjectives, description="Funnel e obiettivi"
    )

    error_message: Optional[str] = Field(
        None, description="Messaggio di errore se lo scraping fallisce"
    )
