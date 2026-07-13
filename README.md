# TTS API

A backend API that converts text into natural-sounding speech, built on top of `edge-tts` (Microsoft Edge's free neural voices) and FastAPI.

## Project structure

```
tts-api/
├── app/
│   ├── main.py              # FastAPI app, middleware, exception handlers
│   ├── config.py            # Settings (env-var driven)
│   ├── schemas.py           # Request/response models + validation
│   ├── core/
│   │   └── exceptions.py    # Domain-specific exceptions
│   ├── routers/
│   │   └── tts.py           # /tts and /voices endpoints
│   └── services/
│       └── tts_service.py   # edge-tts integration logic
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # optional, defaults work out of the box

uvicorn app.main:app --reload --port 8000
```

Then open **http://127.0.0.1:8000/docs** for interactive Swagger docs.

## Endpoints

### `POST /api/v1/tts`
Converts text to speech and returns an MP3 file.

**Request body:**
```json
{
  "text": "Hello! To make this sound more realistic, I've adjusted the speed and pitch.",
  "voice": "en-US-AvaNeural",
  "rate": "-10%",
  "pitch": "+0Hz",
  "volume": "+0%"
}
```

**Response:** `audio/mpeg` binary stream (downloadable as `speech.mp3`)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "en-US-AvaNeural"}' \
  -o speech.mp3
```

### `GET /api/v1/voices`
Lists all available voices, optionally filtered by locale.

```bash
curl http://127.0.0.1:8000/api/v1/voices
curl "http://127.0.0.1:8000/api/v1/voices?locale=en-US"
```

### `GET /health`
Basic liveness check — returns `{"status": "ok"}`.

## Validation rules

- `text`: required, 1–5000 chars, cannot be blank/whitespace
- `voice`: must be a valid edge-tts short name (checked against the live voice list, cached in-process)
- `rate` / `volume`: must match `±N%` (e.g. `-10%`, `+25%`)
- `pitch`: must match `±NHz` (e.g. `+0Hz`, `-5Hz`)

Bad input returns `422` with a field-level error breakdown. Unknown voices return `400`. Upstream synthesis failures return `500`; timeouts return `504`.

## Docker

```bash
docker build -t tts-api .
docker run -p 8000:8000 tts-api
```

## Note on network access

`edge-tts` calls Microsoft's speech service directly (`speech.platform.bing.com`) — this must be reachable outbound wherever you deploy this (a locked-down corporate proxy or firewall will block it, since it's an unofficial API surface, not a published Azure endpoint).

---

## Roadmap: turning this into the full application

This endpoint is the core building block. Here's the fuller plan for a production app around it:

1. **Auth & rate limiting** — API key or JWT auth per user; per-key rate limits (e.g. `slowapi` or a Redis token bucket) to prevent abuse of the free upstream voice service.
2. **Async job queue** — For long text, synthesis can take a few seconds; move to a background task queue (Celery/RQ/Arq + Redis) with a `POST /tts/jobs` → `GET /tts/jobs/{id}` polling pattern instead of blocking the request.
3. **Caching** — Hash `(text, voice, rate, pitch, volume)` and cache the resulting MP3 (S3/local disk + Redis lookup) so repeated phrases don't re-hit the TTS service.
4. **Storage & delivery** — Store generated audio in object storage (S3/R2/GCS) and return a signed URL instead of streaming bytes directly, especially for longer audio or high traffic.
5. **SSML support** — Expose a raw SSML input mode for fine-grained control over pauses, emphasis, and pronunciation, beyond the flat rate/pitch/volume knobs.
6. **Usage metering & billing** — Track characters synthesized per API key for usage-based billing/quotas.
7. **Observability** — Structured logging, request tracing (e.g. OpenTelemetry), and metrics (synthesis latency, error rate, voice popularity).
8. **Multi-provider fallback** — Abstract the `TTSService` interface (already done) so you can add a paid fallback provider (Azure Speech, ElevenLabs, Google Cloud TTS) if edge-tts becomes unreliable at scale, since it's an unofficial/reverse-engineered API.
9. **Frontend** — A simple web UI (voice picker, live preview player, download button) consuming this API.
10. **Deployment** — Containerized deploy (this Dockerfile) behind a reverse proxy (Nginx/Caddy) or on a PaaS (Fly.io, Render, Railway), with horizontal scaling since synthesis is I/O-bound and stateless.

Happy to build out any of these next — job queue + caching is usually the highest-value next step once the basic endpoint is live.
