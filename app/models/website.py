from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl


class WebsiteRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL del sito web da analizzare")


class SiteStructure(BaseModel):
    structure_analysis: List[str] = Field(
        default=["homepage", "chi siamo", "prodotti", "contatti"],
        description="Analisi della struttura del sito: homepage, sezioni, e-commerce, carrello"
    )
    navigation_depth: int = Field(
        default=3,
        description="Profondità della navigazione"
    )
    internal_links: List[str] = Field(
        default=["/home", "/faq", "/termini"],
        description="Link interni e pagine orfane"
    )
    seo_errors: List[str] = Field(
        default=["title duplicato", "redirect loop"],
        description="Errori SEO tecnici"
    )


class NavigationAndLanding(BaseModel):
    user_sources: List[str] = Field(
        default=["social", "direct", "referral"],
        description="Provenienza utenti"
    )
    internal_links_cta: int = Field(
        default=56,
        description="Link interni e CTA"
    )
    external_links_collaborations: bool = Field(
        default=True,
        description="Link esterni e collaborazioni"
    )
    bounce_rate: float = Field(
        default=47.8,
        description="Bounce rate percentuale"
    )
    session_duration: float = Field(
        default=183.4,
        description="Durata media sessione in secondi"
    )
    top_pages: List[str] = Field(
        default=["/prodotti", "/checkout"],
        description="Top pages visitate"
    )


class FunnelAndObjectives(BaseModel):
    funnel_phase: Literal["awareness", "consideration", "conversion"] = Field(
        default="consideration",
        description="Fase funnel prevalente"
    )
    main_objective: Literal["vendita", "posizionamento"] = Field(
        default="vendita",
        description="Obiettivo principale"
    )
    implicit_funnel: str = Field(
        default="frequentazione pagine prodotto > checkout",
        description="Funnel implicito da comportamento"
    )


class ToneOfVoice(BaseModel):
    social_site_coherence: bool = Field(
        default=True,
        description="Coerenza social-sito"
    )
    perceived_style: Literal["serio", "premium", "casual", "professionale", "minimale"] = Field(
        default="premium",
        description="Stile percepito"
    )


class UserExperience(BaseModel):
    navigation_fluidity: Literal["ottima", "buona", "sufficiente", "scarsa"] = Field(
        default="ottima",
        description="Navigazione fluida"
    )
    perceived_design: Literal["premium", "minimale", "moderno", "classico", "outdated"] = Field(
        default="premium",
        description="Design percepito"
    )
    technical_performance: List[Dict[str, str]] = Field(
        default=[
            {"LCP": "1340ms"},
            {"FID": "40ms"},
            {"CLS": "0.07"}
        ],
        description="Performance tecnica (Core Web Vitals)"
    )


class WebsiteScrapingResult(BaseModel):
    url: str = Field(..., description="URL analizzato")
    scraping_date: str = Field(..., description="Data dello scraping")
    
    site_structure: SiteStructure = Field(
        default_factory=SiteStructure,
        description="Struttura del sito"
    )
    navigation_landing: NavigationAndLanding = Field(
        default_factory=NavigationAndLanding,
        description="Navigazione e landing"
    )
    funnel_objectives: FunnelAndObjectives = Field(
        default_factory=FunnelAndObjectives,
        description="Funnel e obiettivi"
    )
    tone_of_voice: ToneOfVoice = Field(
        default_factory=ToneOfVoice,
        description="Tone of Voice"
    )
    user_experience: UserExperience = Field(
        default_factory=UserExperience,
        description="Esperienza utente / UX"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Messaggio di errore se lo scraping fallisce"
    )