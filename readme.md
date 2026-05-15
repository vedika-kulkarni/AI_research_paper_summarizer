# PaperMind 📄

AI-powered research paper summarizer.  
**Stack:** Python · FastAPI · Claude claude-sonnet-4-20250514 · Vanilla HTML/JS

```
papermind/
├── backend/
│   ├── main.py            ← FastAPI app
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── index.html         ← Single-file UI
```

---

## 1 · Prerequisites

- Python 3.10+
- An Anthropic API key → https://console.anthropic.com

---

## 2 · Local setup

```bash
# Clone / unzip the project, then:

cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and paste your key
```

**.env**
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

---

## 3 · Run locally

```bash
# From the backend/ folder (venv active):
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** → the frontend is served automatically.

> The backend mounts `../frontend/` as static files, so the HTML is served
> at the root. No separate server needed.

---

## 4 · Deploy options

### A) VPS / bare server (Ubuntu)

```bash
# Install deps
sudo apt update && sudo apt install -y python3-pip python3-venv nginx

# Set up app
cd /opt && git clone <your-repo> papermind
cd papermind/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env   # paste API key

# Systemd service
sudo tee /etc/systemd/system/papermind.service <<EOF
[Unit]
Description=PaperMind FastAPI
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/papermind/backend
ExecStart=/opt/papermind/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
EnvironmentFile=/opt/papermind/backend/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now papermind

# Nginx reverse proxy
sudo tee /etc/nginx/sites-available/papermind <<EOF
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 20M;   # allow PDF uploads

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 120s;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/papermind /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Add HTTPS with: `sudo certbot --nginx -d yourdomain.com`

---

### B) Railway (free tier)

```bash
# Install Railway CLI
npm i -g @railway/cli && railway login

cd papermind
railway init
railway up

# Set env var in Railway dashboard → Variables → ANTHROPIC_API_KEY
```

Add a `Procfile` in `backend/`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### C) Render (free tier)

1. Push repo to GitHub
2. New Web Service → connect repo
3. **Root dir:** `backend`
4. **Build command:** `pip install -r requirements.txt`
5. **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Environment → `ANTHROPIC_API_KEY=sk-ant-...`

---

### D) Docker

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
cd backend
docker build -t papermind .
docker run -p 8000:8000 --env-file .env \
  -v $(pwd)/../frontend:/app/../frontend \
  papermind
```

Or with docker-compose:

```yaml
# docker-compose.yml (project root)
version: "3.9"
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    volumes:
      - ./frontend:/app/../frontend
```

```bash
docker compose up -d
```

---

## 5 · API endpoints

| Method | Path | Body |
|--------|------|------|
| POST | `/summarize/url`  | `{ url, depth, audience }` |
| POST | `/summarize/text` | `{ text, depth, audience }` |
| POST | `/summarize/pdf`  | multipart: `file`, `depth`, `audience` |
| GET  | `/health`         | — |

**depth:** `quick` / `standard` / `deep`  
**audience:** `expert` / `researcher` / `student` / `layperson`

---

## 6 · Customization

| Thing | Where |
|-------|-------|
| Claude model | `MODEL` constant in `main.py` |
| Max tokens | `max_tokens` in `call_anthropic()` |
| Summary sections | `build_system_prompt()` in `main.py` |
| Colors / fonts | CSS `:root` in `frontend/index.html` |
| PDF size limit | `client_max_body_size` in nginx config |

---

MIT License