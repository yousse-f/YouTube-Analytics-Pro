"""
Endpoint API per l'Analisi di Siti Web.

Route FastAPI per la funzionalità di analisi automatica dei siti web.
Fornisce endpoint per l'analisi completa di business intelligence.
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.models import (
    WebsiteAnalysisRequest,
    WebsiteAnalysisResult,
    HealthCheckResponse,
    ErrorResponse
)
from app.services.website_analyzer import WebsiteAnalyzer
from app.security.api_key import verify_api_key
from app.utils.logger import setup_logger
from app.config import settings

# Configurazione logger per il modulo API
logger = setup_logger(__name__)
router = APIRouter()

# Istanza globale dell'analizzatore (ottimizzazione performance)
analyzer = WebsiteAnalyzer()

# Tempo di avvio per calcolo uptime del servizio
app_start_time = time.time()


@router.post(
    "/analyze",
    response_model=WebsiteAnalysisResult,
    summary="Analisi Completa Sito Web",
    description="Esegue un'analisi completa di business intelligence di un sito web includendo informazioni aziendali, tecnologie, SEO e metriche di performance.",
    dependencies=[Depends(verify_api_key)]
)
async def analyze_website(request: WebsiteAnalysisRequest) -> WebsiteAnalysisResult:
    """
    Analizza un sito web e restituisce risultati completi di business intelligence.
    
    Questo endpoint esegue un'analisi dettagliata dell'URL fornito, estraendo:
    - Informazioni aziendali (nome company, contatti, descrizione)
    - Rilevamento stack tecnologico (framework, librerie, CMS)
    - Metriche SEO (title tag, meta description, tag H1)
    - Metriche di performance (tempo risposta, dimensione pagina)
    - Analisi contenuti (conteggio parole, lingua, argomenti chiave)
    
    Richiede autenticazione tramite API Key nell'header X-API-Key.
    
    Args:
        request: Parametri di richiesta per l'analisi del sito web
        
    Returns:
        WebsiteAnalysisResult: Risultati completi dell'analisi
        
    Raises:
        HTTPException: In caso di errori di timeout, connessione o server
    """
    request_start_time = time.time()
    
    logger.info(
        "Richiesta di analisi sito web ricevuta",
        extra={
            "url": str(request.url),
            "profondita_analisi": request.analysis_depth,
            "includi_sottodomini": request.include_subdomains,
            "max_pagine": request.max_pages
        }
    )
    
    try:
        # Esecuzione dell'analisi completa
        result = await analyzer.analyze_website(request)
        
        request_duration = time.time() - request_start_time
        
        logger.info(
            "Analisi sito web completata con successo",
            extra={
                "url": str(request.url),
                "successo": result.analysis_success,
                "punteggio_confidenza": result.confidence_score,
                "durata_secondi": round(request_duration, 2),
                "tecnologie_trovate": len(result.technologies),
                "pagine_analizzate": result.pages_analyzed
            }
        )
        
        return result
        
    except Exception as e:
        request_duration = time.time() - request_start_time
        
        logger.error(
            "Analisi sito web fallita",
            extra={
                "url": str(request.url),
                "errore": str(e),
                "tipo_errore": type(e).__name__,
                "durata_secondi": round(request_duration, 2)
            },
            exc_info=True
        )
        
        # Restituisce errore HTTP appropriato basato sul tipo di errore
        if "timeout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Timeout durante l'analisi del sito web: {str(e)}"
            )
        elif "connection" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Impossibile connettersi al sito web: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analisi fallita a causa di errore interno: {str(e)}"
            )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Controllo Stato Servizio",
    description="Verifica lo stato di salute del servizio Website Analyzer API."
)
async def health_check() -> HealthCheckResponse:
    """
    Endpoint di controllo stato per il monitoraggio del servizio.
    
    Restituisce lo stato attuale, uptime e informazioni sulla versione del servizio.
    Questo endpoint non richiede autenticazione per facilità di monitoraggio.
    
    Returns:
        HealthCheckResponse: Stato corrente del servizio con timestamp e uptime
    """
    uptime_seconds = time.time() - app_start_time
    
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime_seconds=round(uptime_seconds, 2)
    )


@router.get(
    "/status",
    summary="Stato Dettagliato Servizio",
    description="Ottieni informazioni dettagliate sullo stato del servizio e configurazione attiva."
)
async def service_status():
    """
    Endpoint di stato del servizio con dettagli di configurazione.
    
    Restituisce la configurazione attuale del servizio e informazioni di runtime.
    Utile per debugging e monitoraggio avanzato del sistema.
    Non richiede autenticazione per accessibilità.
    
    Returns:
        dict: Informazioni complete su servizio, configurazione e stato operativo
    """
    uptime_seconds = time.time() - app_start_time
    
    return {
        "servizio": "Website Analyzer API",
        "versione": "1.0.0",
        "stato": "operativo",
        "uptime_secondi": round(uptime_seconds, 2),
        "configurazione": {
            "versione_api": settings.API_VERSION,
            "profondita_analisi_default": settings.ANALYSIS_DEPTH,
            "max_pagine_default": settings.MAX_PAGES_TO_ANALYZE,
            "timeout_richiesta": settings.REQUEST_TIMEOUT,
            "tentativi_retry": settings.RETRY_ATTEMPTS,
            "dimensione_massima_pagina": settings.MAX_PAGE_SIZE,
            "user_agent": settings.USER_AGENT
        },
        "metriche_runtime": {
            "istanza_analyzer_attiva": analyzer is not None,
            "timestamp_avvio": app_start_time,
            "timestamp_corrente": time.time()
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
