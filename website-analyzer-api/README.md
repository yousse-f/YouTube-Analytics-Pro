# Website Analyzer API

🔍 **Microservizio FastAPI per analisi completa di siti web e business intelligence.**

## 🎯 Funzionalità

- **🏢 Business Intelligence**: Estrazione automatica di informazioni aziendali
- **🔧 Technology Detection**: Rilevamento stack tecnologico utilizzato
- **📊 SEO Analysis**: Analisi metriche SEO e ottimizzazione
- **⚡ Performance Metrics**: Misurazione performance e tempi di risposta
- **📝 Content Analysis**: Analisi contenuti e argomenti chiave
- **🔐 API Key Authentication**: Sicurezza endpoint con autenticazione
- **🔄 Retry Mechanism**: Resilienza automatica per chiamate esterne
- **📋 Structured Logging**: Sistema logging centralizzato e strutturato

## 🚀 Quick Start

### Con Docker (Raccomandato)

```bash
# 1. Configura environment
cp .env.example .env
# Modifica .env con le tue configurazioni

# 2. Build e avvia il servizio
docker build -t website-analyzer-api .
docker run -p 8003:8003 --env-file .env website-analyzer-api
```

### Con Python

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Configura environment
cp .env.example .env
# Modifica .env con le tue configurazioni

# 3. Avvia il servizio
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

## 📖 API Documentation

Il servizio sarà disponibile su `http://localhost:8003`

- **Swagger UI**: `http://localhost:8003/api/v1/docs`
- **ReDoc**: `http://localhost:8003/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8003/api/v1/openapi.json`

## 🔧 Endpoint Principali

### 🔍 Website Analysis

```bash
POST /api/v1/website/analyze
Content-Type: application/json
X-API-Key: your_api_key_here

{
  "url": "https://example.com",
  "analysis_depth": "standard",
  "include_subdomains": false,
  "max_pages": 5
}
```

**Response:**
```json
{
  "analyzed_url": "https://example.com",
  "analysis_depth": "standard",
  "analysis_timestamp": "2025-08-10T14:30:00Z",
  "analysis_duration_seconds": 15.5,
  "business_info": {
    "company_name": "Example Corp",
    "industry": "Technology",
    "description": "Leading tech company",
    "contact_email": "info@example.com"
  },
  "technologies": [
    {
      "name": "React",
      "category": "Frontend Framework",
      "confidence": 0.95
    }
  ],
  "seo_metrics": {
    "title_tag": "Example Corp - Leading Technology Solutions",
    "ssl_enabled": true
  },
  "analysis_success": true,
  "confidence_score": 0.85
}
```

### 💚 Health Check

```bash
GET /api/v1/website/health
```

## ⚙️ Configurazione

### Environment Variables (.env)

```bash
# API Security
API_KEY=your_website_analyzer_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8003
API_VERSION=v1
API_TITLE=Website Analyzer API

# CORS Settings
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-API-Key

# Analysis Settings
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
REQUEST_TIMEOUT=30
MAX_PAGE_SIZE=10485760
ANALYSIS_DEPTH=standard
MAX_PAGES_TO_ANALYZE=5

# Retry Configuration
RETRY_ATTEMPTS=3
RETRY_WAIT_SECONDS=2
RETRY_BACKOFF_MULTIPLIER=1.5
RETRY_MAX_WAIT_SECONDS=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=detailed
LOG_TO_FILE=false
LOG_FILE_PATH=logs/website-analyzer.log
```

## 🔐 Sicurezza

### API Key Authentication

Tutti gli endpoint di analisi sono protetti con API Key authentication:

```bash
curl -X POST "http://localhost:8003/api/v1/website/analyze" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### CORS Configuration

Configurazione CORS restrittiva per sicurezza:
- Solo domini specifici autorizzati
- Header specifici ammessi
- Metodi HTTP limitati

## 📊 Analisi Supportate

### 🏢 Business Intelligence
- **Company Name**: Estrazione automatica nome azienda
- **Industry Detection**: Rilevamento settore di appartenenza
- **Contact Information**: Email e telefono di contatto
- **Company Description**: Descrizione attività aziendale

### 🔧 Technology Stack
- **Frontend Frameworks**: React, Vue.js, Angular
- **JavaScript Libraries**: jQuery, Bootstrap
- **CMS Detection**: WordPress, Shopify
- **Analytics Tools**: Google Analytics, tracking scripts

### 📊 SEO Metrics
- **Meta Tags**: Title, description, keywords
- **Header Tags**: H1, H2, struttura contenuti
- **SSL Status**: Verifica certificato HTTPS
- **Technical SEO**: Robots.txt, sitemap

### ⚡ Performance
- **Response Time**: Tempo risposta server
- **Page Size**: Dimensione pagina in bytes
- **Status Codes**: Codici HTTP di risposta

## 🛠️ Sviluppo

### Struttura Progetto

```
website-analyzer-api/
├── app/
│   ├── api/                    # Endpoint FastAPI
│   ├── services/               # Business logic
│   ├── models/                 # Pydantic models
│   ├── utils/                  # Utility (logging, retry, HTTP)
│   ├── security/               # Authentication
│   ├── config.py               # Configurazione centralizzata
│   └── main.py                 # FastAPI application
├── requirements.txt            # Dependencies Python
├── Dockerfile                  # Container definition
├── .env.example               # Template configurazione
└── README.md                  # Documentazione
```

### Testing

```bash
# Test manuale endpoint
curl -X GET "http://localhost:8003/health"

# Test analisi (con API key)
curl -X POST "http://localhost:8003/api/v1/website/analyze" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 🚀 Production Ready Features

- ✅ **API Key Authentication** - Sicurezza robusta
- ✅ **CORS Configuration** - Sicurezza cross-origin
- ✅ **Environment Variables** - Zero hardcoded secrets
- ✅ **Structured Logging** - Observability completa
- ✅ **Retry Mechanism** - Resilienza automatica
- ✅ **Health Checks** - Monitoraggio servizio
- ✅ **Error Handling** - Gestione errori robusta
- ✅ **Input Validation** - Validazione Pydantic
- ✅ **Docker Support** - Containerizzazione

## 📈 Roadmap

### Fase 2 - Advanced Features
- **Competitive Analysis**: Comparazione con competitor
- **SEO Scoring**: Punteggio SEO automatico
- **Social Media Detection**: Presenza social media
- **E-commerce Analysis**: Rilevamento piattaforme e-commerce

### Fase 3 - AI Enhancement
- **NLP Content Analysis**: Analisi sentiment e topics
- **Visual Analysis**: Computer vision per design
- **Predictive Analytics**: Predizione performance
- **Automated Insights**: Report automatici

## 🤝 Contributi

Il microservizio è parte dell'ecosistema SCS Data Management. Per contributi:
1. Fork del repository
2. Feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 Licenza

Questo progetto è parte del sistema SCS Data Management.

---

**🔗 Servizi Correlati:**
- [`instagram-analytics-api/`](../instagram-analytics-api/) - Analisi Instagram
- [`youtube-scraper-api/`](../app/) - Scraping YouTube

**📚 Documentazione Completa:** Swagger UI disponibile su `/api/v1/docs`
