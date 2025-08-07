# SCS Data Management - Web & Instagram Scraping Service

Microservizio Python basato su FastAPI per lo scraping e l'analisi di siti web e profili Instagram pubblici.

## Requisiti

- Python 3.11+
- Docker 

## Installazione

### Con Python

1. Clona il repository:
```bash
cd scs-data-management
```

2. Crea un ambiente virtuale:
```bash
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

4. Configura le variabili d'ambiente:
```bash
cp .env.example .env  
# Modifica .env con i tuoi token Crawlbase e configurazioni
```

5. Avvia il servizio:
```bash
uvicorn app.main:app --reload
```

### Con Docker

1. Costruisci l'immagine:
```bash
docker-compose build
```

2. Avvia il servizio:
```bash
docker-compose up
```

## Utilizzo

Il servizio sarà disponibile su `http://localhost:8000`

### Documentazione API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints principali

#### 1. Website Scraping
```bash
POST /api/v1/scrape/website
Content-Type: application/json

{
  "url": "https://example.com"
}
```

#### 2. YouTube Scraping (🔐 Protected with API Key)
```bash
POST /api/v1/scrape/youtube
Content-Type: application/json
X-API-Key: your_api_key_here

{
  "url": "https://www.youtube.com/@channel_name"
}
```

#### 3. Instagram Scraping
```bash
POST /api/v1/scrape/instagram
Content-Type: application/json

{
  "username": "instagram_username"
}
```

### Esempi con cURL

YouTube scraping (con API Key):
```bash
curl -X POST "http://localhost:8000/api/v1/scrape/youtube" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"url": "https://www.youtube.com/@channel_name"}'
```
Website scraping:
```bash
curl -X POST "http://localhost:8000/api/v1/scrape/website" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Instagram scraping:
```bash
curl -X POST "http://localhost:8000/api/v1/scrape/instagram" \
  -H "Content-Type: application/json" \
  -d '{"username": "cristiano"}'
```

## Struttura del Progetto

```
scs-data-management/
├── app/
│   ├── main.py                    # Entry point FastAPI
│   ├── config.py                  # Configurazione
│   ├── api/                       # API endpoints
│   │   ├── website_scraper.py
│   │   └── instagram_scraper.py
│   ├── services/                  # Business logic
│   │   ├── website.py
│   │   └── instagram.py
│   ├── models/                    # Pydantic models
│   │   ├── website.py
│   │   └── instagram.py
│   └── utils/                     # Utilities
│       ├── logger.py
│       ├── html_parser.py
│       └── http_client.py
├── .env                           # Variabili d'ambiente
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Configurazione

Le principali variabili d'ambiente configurabili in `.env`:

### API Configuration
- `API_HOST`: Host dell'API (default: 0.0.0.0)
- `API_PORT`: Porta dell'API (default: 8000)
- `API_KEY`: Chiave API per autenticazione endpoint protetti

### CORS Security
- `FRONTEND_URL`: URL principale del frontend
- `CORS_ORIGINS`: Lista domini autorizzati (separati da virgola)
- `CORS_ALLOW_CREDENTIALS`: Abilita credenziali CORS (true/false)
- `CORS_ALLOW_METHODS`: Metodi HTTP ammessi (GET,POST,PUT,DELETE,OPTIONS)
- `CORS_ALLOW_HEADERS`: Header ammessi (Content-Type,Authorization,X-API-Key)

### Logging Configuration
- `LOG_LEVEL`: Livello di logging (DEBUG, INFO, WARNING, ERROR)
- `LOG_FORMAT`: Formato log (detailed/json) - usa JSON per produzione
- `LOG_TO_FILE`: Abilita logging su file (true/false)
- `LOG_FILE_PATH`: Percorso file di log (default: logs/app.log)

### Retry Configuration
- `RETRY_ATTEMPTS`: Numero massimo di tentativi per chiamate esterne (default: 3)
- `RETRY_WAIT_SECONDS`: Tempo di attesa iniziale tra i retry in secondi (default: 2)
- `RETRY_BACKOFF_MULTIPLIER`: Moltiplicatore per backoff esponenziale (default: 1.5)
- `RETRY_MAX_WAIT_SECONDS`: Tempo massimo di attesa tra i retry (default: 10)

### Scraping Configuration
- `USER_AGENT`: User agent per le richieste HTTP
- `REQUEST_TIMEOUT`: Timeout richieste in secondi (default: 30)
- `LOG_LEVEL`: Livello di logging (default: INFO)

### External Services
- `CRAWLBASE_NORMAL_TOKEN`: Token Crawlbase per scraping normale
- `CRAWLBASE_JS_TOKEN`: Token Crawlbase per scraping JavaScript

## Sicurezza

### API Key Authentication

L'endpoint YouTube è protetto con API Key authentication. Per accedere:

1. Configura `API_KEY` nel file `.env`
2. Includi l'header `X-API-Key` nelle richieste:

```bash
curl -X POST "http://localhost:8000/api/v1/scrape/youtube" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/@channel"}'
```

**Risposte di errore:**
- `401 Unauthorized`: API Key mancante o non valida
- `422 Unprocessable Entity`: Errore di validazione dei dati

## Note Importanti

### 🔐 Security Features

1. **API Key Protection**: L'endpoint YouTube è protetto con API Key obbligatoria:
   ```bash
   curl -H "X-API-Key: your_api_key_here" ...
   ```

2. **CORS Security**: Configurazione CORS restrittiva:
   - Solo domini specifici autorizzati (no wildcard `*`)
   - Header specifici ammessi per sicurezza
   - Metodi HTTP limitati ai necessari
   
3. **Environment Variables**: Tutte le configurazioni sensibili in `.env`:
   - Token API esterni
   - Chiavi di autenticazione
   - Configurazioni CORS

### � Resilience & Reliability

Il microservizio implementa meccanismi di resilienza per la produzione:

1. **Automatic Retry**: Retry automatico con backoff esponenziale per:
   - Chiamate HTTP esterne (API Crawlbase, ecc.)
   - Operazioni Selenium WebDriver
   - Connessioni di rete temporaneamente non disponibili

2. **Retry Configuration**:
   ```env
   RETRY_ATTEMPTS=3                 # Max 3 tentativi
   RETRY_WAIT_SECONDS=2             # 2s attesa iniziale
   RETRY_BACKOFF_MULTIPLIER=1.5     # Incremento 1.5x
   RETRY_MAX_WAIT_SECONDS=10        # Max 10s di attesa
   ```

3. **Structured Logging**: Ogni operazione di retry viene tracciata con:
   - Numero tentativo
   - Tipo errore
   - Tempo di attesa
   - Stack trace dettagliato

### �📝 Development vs Production

**Development** (localhost):
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Production**:
```env
CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
```

### 🧪 Testing CORS

Per testare CORS dal browser, apri `test-cors.html` da un server locale su porta 3000 o 5173.

---

### 📋 Logging

Il microservizio utilizza un sistema di logging centralizzato e strutturato:

**Development** (formato human-readable):
```env
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
LOG_TO_FILE=false
```

**Production** (formato JSON per aggregatori):
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
```

**Livelli disponibili:**
- `DEBUG`: Informazioni dettagliate per debugging
- `INFO`: Informazioni generali di operazione
- `WARNING`: Avvisi che non bloccano l'operazione
- `ERROR`: Errori che richiedono attenzione

**Best practices:**
- Tutti i moduli usano `setup_logger(__name__)`
- Nessun `print()` nel codice di produzione
- Logging strutturato con parametri: `logger.info("Message: %s", value)`
- Stack trace automatici con `exc_info=True`

---

## Note Tecniche Precedenti

1. **Instagram Scraping**: Attualmente i dati Instagram sono simulati per demo. In produzione sarà necessario:
   - Utilizzare l'API ufficiale di Instagram
   - O implementare un sistema di scraping più sofisticato
   - Rispettare i termini di servizio di Instagram

2. **Rate Limiting**: Non implementato in questa versione. In produzione considerare:
   - Limiti per IP/utente
   - Queue per richieste
   - Caching dei risultati

3. **Performance**: Per siti web molto grandi, considerare:
   - Implementare paginazione
   - Scraping incrementale
   - Background jobs per analisi lunghe

## Testing

Per testare manualmente gli endpoint:

1. Avvia il servizio
2. Vai su `http://localhost:8000/docs`
3. Usa l'interfaccia Swagger per testare gli endpoint

## Troubleshooting

### Errore di connessione
- Verifica che il servizio sia in esecuzione
- Controlla che la porta 8000 non sia già in uso

### Errore di scraping
- Verifica che l'URL/username sia valido
- Controlla i log per dettagli: `docker-compose logs -f`

### CORS issues
- Assicurati che `FRONTEND_URL` sia configurato correttamente in `.env`

## Licenza

Proprietario