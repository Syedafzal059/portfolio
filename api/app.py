import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Portfolio Ask API", version="0.1.0")

_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
# Explicit list (e.g. production custom domain) plus regex so every *.vercel.app preview
# still works — a single typo or new Vercel URL used to break CORS and show "Network error" in the browser.
_cors_kw = {
    "allow_methods": ["POST", "GET", "OPTIONS"],
    "allow_headers": ["*"],
}
if not _origins_env or _origins_env == "*":
    _cors_kw["allow_origins"] = ["*"]
    _cors_kw["allow_credentials"] = False
else:
    _cors_kw["allow_origins"] = [o.strip() for o in _origins_env.split(",") if o.strip()]
    _cors_kw["allow_credentials"] = True
    _cors_kw["allow_origin_regex"] = (
        r"^https://[\w.-]+\.vercel\.app$"
        r"|^http://localhost(:\d+)?$"
        r"|^http://127\.0\.0\.1(:\d+)?$"
    )

app.add_middleware(CORSMiddleware, **_cors_kw)

_api_key = os.getenv("OPENAI_API_KEY")
_client = OpenAI(api_key=_api_key) if _api_key else None

PORTFOLIO_CONTEXT = """
S M Afzal Hashmi — Senior AI Engineer, Bangalore, India.
Education: MS Signal Processing, IIT Delhi (CGPA 9.3/10); B.Tech ECE, NIET Noida (~80%).

Current: Apexon (May 2024–present), Senior Data Scientist / Team Lead — agentic AI for life sciences
(clinical protocol configuration weeks→hours), AI recruitment platform (~60% hiring time reduction, ~80% HR tasks automated),
agentic action chatbot with multi-step reasoning and tool integrations. Stack highlights: LangGraph, FastAPI, RAG, LLM orchestration.

Prior: Ascendum Solutions (May 2023–Feb 2024), Senior Data Scientist — LayoutLM, BERT, GAN-based denoising, OCR, document AI.

Prior: IIT Delhi Bharti School (Aug 2018–Apr 2023), Senior Research Fellow — India DoT 5G testbed (mMTC/NB-IoT), nationwide 5G mMTC
workshops (200+ researchers), LSTM air-quality monitoring, Indian Mobile Congress 2019 & 2022.

Selected builds (GitHub: Syedafzal059): framework-free autonomous agent; LangGraph long-horizon agent; MCP graph UI for agents;
production support agent (RAG, LLM-as-judge, tracing); LoRA/QLoRA fine-tuning pipeline; FastAPI LLM orchestration API with routing/cache/failover.

Research: AI-powered electronic stethoscope / respiratory ML pipeline at IIT Delhi; collaborator Prof. Monika Aggarwal (EE).

Writing: Medium @syedafzal059 — (1) "Your LLM Is Not the Problem — Your Harness Is" (harness/orchestration vs model); (2) "The RAG Optimization Playbook: From Slow and Noisy to Fast and Accurate" (RAG pipelines, retrieval quality, latency).

Contact: syedafzal059@gmail.com; LinkedIn: linkedin.com/in/saiyad-mohammad-afzal-hashmi-583955115; GitHub: Syedafzal059. Hackathon: Runner Up — Agentic AI Hackathon, Apexon (2025).
Only use facts from this context. If something is not covered, say you do not have that detail in Afzal's public portfolio context.
"""

SYSTEM_PROMPT = f"""You are a sharp, confident AI assistant representing S M Afzal Hashmi (Afzal) to recruiters and engineers.

Rules:
- Be concise: default to ~4–8 sentences or tight bullets; go deeper only if the user explicitly asks for more detail.
- Ground every claim in the context below; do not invent employers, dates, metrics, or projects not listed.
- If asked for something outside the context, say clearly that it is not in the portfolio brief and suggest contacting Afzal via email/LinkedIn.
- Tone: senior engineer — clear, impact-oriented, no fluff.

Context:
{PORTFOLIO_CONTEXT}
"""


class Query(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/")
def health():
    return {"status": "ok", "service": "portfolio-ask"}


@app.post("/ask")
def ask_ai(q: Query):
    if not _client:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server.")

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q.question.strip()},
            ],
            max_tokens=320,
            temperature=0.25,
        )
        answer = response.choices[0].message.content or ""
        return {"answer": answer.strip()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream model error") from exc
