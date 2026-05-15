import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

app = FastAPI(title="PaperMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve frontend static files ──────────────────────────────────────────────
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))


# ── Helpers ──────────────────────────────────────────────────────────────────

def build_system_prompt(depth: str, audience: str) -> str:
    audience_map = {
        "expert":     "a domain expert with deep technical knowledge",
        "researcher": "a fellow researcher familiar with the field",
        "student":    "a graduate student learning the area",
        "layperson":  "a curious non-expert general audience member",
    }
    depth_map = {
        "quick":    "Provide: TL;DR, Key Contributions, and one Key Takeaway.",
        "standard": "Provide all sections: TL;DR, Key Contributions, Methodology, Results & Metrics, Limitations, and Key Takeaway.",
        "deep":     "Provide all sections in extended depth: TL;DR, Key Contributions, Methodology (detailed), Results & Metrics (with numbers), Limitations & Future Work, Novelty vs Prior Art, Practical Implications, and Key Takeaway.",
    }
    return f"""You are PaperMind, an expert AI research paper summarizer.
Audience: {audience_map.get(audience, 'a researcher')}.
{depth_map.get(depth, depth_map['standard'])}

Respond ONLY with a valid JSON object (no markdown, no backticks, no preamble) with this exact structure:
{{
  "title": "Paper title or best guess",
  "year": "Year if found, else null",
  "authors": "Authors string if found, else null",
  "tldr": "1-2 sentence plain-language summary",
  "contributions": ["bullet 1", "bullet 2"],
  "methodology": "paragraph or null if not requested",
  "results": ["metric/finding 1"] or null,
  "limitations": ["limit 1"] or null,
  "novelty": "paragraph or null",
  "implications": "paragraph or null",
  "takeaway": "The single most important insight from this paper"
}}"""


async def call_anthropic(messages: list, use_search: bool = False) -> dict:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set in .env")

    body = {
        "model": MODEL,
        "max_tokens": 2000,
        "messages": messages,
    }
    if use_search:
        body["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=body,
        )

    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)

    data = resp.json()
    text = "".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
    return text


# ── Routes ───────────────────────────────────────────────────────────────────

class URLRequest(BaseModel):
    url: str
    depth: str = "standard"
    audience: str = "researcher"


class TextRequest(BaseModel):
    text: str
    depth: str = "standard"
    audience: str = "researcher"


@app.post("/summarize/url")
async def summarize_url(req: URLRequest):
    system = build_system_prompt(req.depth, req.audience)
    messages = [
        {
            "role": "user",
            "content": f"{system}\n\nPaper URL or DOI: {req.url}\n\nFetch and read this paper, then summarize it according to the instructions above.",
        }
    ]
    raw = await call_anthropic(messages, use_search=True)
    return {"raw": raw}


@app.post("/summarize/text")
async def summarize_text(req: TextRequest):
    system = build_system_prompt(req.depth, req.audience)
    messages = [
        {
            "role": "user",
            "content": f"{system}\n\nPaper text:\n\n{req.text}",
        }
    ]
    raw = await call_anthropic(messages, use_search=False)
    return {"raw": raw}


@app.post("/summarize/pdf")
async def summarize_pdf(
    file: UploadFile = File(...),
    depth: str = Form("standard"),
    audience: str = Form("researcher"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    b64 = base64.b64encode(contents).decode()
    system = build_system_prompt(depth, audience)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
                },
                {"type": "text", "text": system},
            ],
        }
    ]
    raw = await call_anthropic(messages, use_search=False)
    return {"raw": raw}


@app.get("/health")
def health():
    key_set = bool(ANTHROPIC_API_KEY)
    return {"status": "ok", "api_key_set": key_set, "model": MODEL}
    