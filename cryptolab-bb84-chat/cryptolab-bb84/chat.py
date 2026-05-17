"""CryptoLab BB84 Chat API.

Run locally with:

    uvicorn chat:app --reload --port 8000

Environment variables:

    CHAT_API_KEY              Optional shared secret. Defaults to "dev-chat-key".
    CHAT_SIMULATION_MODE      "true" by default. Set to "false" for real OpenAI calls.
    SIMULATED_LATENCY_MS      Artificial simulation latency, default 250.
    OPENAI_API_KEY            Required only when CHAT_SIMULATION_MODE=false.

The endpoint is intentionally lightweight for hackathon use. It provides a safe
simulation mode, optional OpenAI integration, streaming Server-Sent Events, basic
per-IP rate limiting, and in-memory metrics suitable for frontend demos.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from statistics import quantiles
from typing import AsyncGenerator, Deque

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

CHAT_API_KEY = os.getenv("CHAT_API_KEY", "dev-chat-key")
SIMULATION_MODE = os.getenv("CHAT_SIMULATION_MODE", "true").lower() != "false"
SIMULATED_LATENCY_MS = int(os.getenv("SIMULATED_LATENCY_MS", "250"))


@dataclass
class ChatCall:
    timestamp: float
    prompt_chars: int
    response_chars: int
    latency_ms: float
    model: str
    success: bool
    tokens_prompt: int
    tokens_completion: int
    estimated_cost_usd: float
    error: str = ""


class ChatMetrics:
    """Small in-memory collector for demo observability."""

    def __init__(self, maxlen: int = 500) -> None:
        self.calls: Deque[ChatCall] = deque(maxlen=maxlen)

    def add(self, call: ChatCall) -> None:
        self.calls.append(call)

    def summary(self) -> dict:
        calls = list(self.calls)
        if not calls:
            return {"total_calls": 0, "p95_latency_ms": 0.0, "error_rate": 0.0, "recent": []}
        latencies = [c.latency_ms for c in calls]
        p95 = quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        errors = sum(1 for c in calls if not c.success)
        return {
            "total_calls": len(calls),
            "p95_latency_ms": round(p95, 2),
            "error_rate": round(errors / len(calls), 4),
            "total_estimated_cost_usd": round(sum(c.estimated_cost_usd for c in calls), 6),
            "recent": [asdict(c) for c in calls[-10:]],
        }


METRICS = ChatMetrics()
RATE_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    model: str = "gpt-4.1-mini"
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    model: str
    latency_ms: float
    tokens_used: int
    estimated_cost_usd: float
    simulation_mode: bool


app = FastAPI(title="CryptoLab BB84 Chat API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if CHAT_API_KEY and x_api_key != CHAT_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header")


async def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = RATE_BUCKETS[ip]
    while bucket and now - bucket[0] > 1.0:
        bucket.popleft()
    if len(bucket) >= 10:
        raise HTTPException(status_code=429, detail="Rate limit exceeded: 10 requests per second")
    bucket.append(now)


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))


def simulation_answer(prompt: str) -> str:
    return (
        "CryptoLab assistant: "
        "For BB84, compare Alice and Bob's sampled sifted bits to estimate QBER. "
        "If QBER rises above the safety threshold, treat the channel as compromised. "
        f"Your question was: {prompt[:500]}"
    )


async def generate_answer(prompt: str, model: str) -> str:
    if SIMULATION_MODE:
        await asyncio.sleep(SIMULATED_LATENCY_MS / 1000)
        return simulation_answer(prompt)

    try:
        from openai import AsyncOpenAI
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise HTTPException(status_code=500, detail="Install openai or enable CHAT_SIMULATION_MODE=true") from exc

    client = AsyncOpenAI()
    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a concise BB84 quantum cryptography teaching assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content or ""


async def stream_words(text: str) -> AsyncGenerator[str, None]:
    for word in text.split():
        yield f"data: {word}\\n\\n"
        await asyncio.sleep(0.035)
    yield "data: [DONE]\\n\\n"


@app.post("/v1/chat/completions", dependencies=[Depends(require_api_key), Depends(rate_limit)], response_model=None)
async def chat_completions(payload: ChatRequest):
    start = time.perf_counter()
    try:
        answer = await generate_answer(payload.prompt, payload.model)
        latency_ms = (time.perf_counter() - start) * 1000
        prompt_tokens = estimate_tokens(payload.prompt)
        completion_tokens = estimate_tokens(answer)
        cost = (prompt_tokens + completion_tokens) * 0.000002
        METRICS.add(ChatCall(time.time(), len(payload.prompt), len(answer), latency_ms, payload.model, True, prompt_tokens, completion_tokens, cost))
        if payload.stream:
            return StreamingResponse(stream_words(answer), media_type="text/event-stream")
        return ChatResponse(
            response=answer,
            model=payload.model,
            latency_ms=round(latency_ms, 2),
            tokens_used=prompt_tokens + completion_tokens,
            estimated_cost_usd=round(cost, 6),
            simulation_mode=SIMULATION_MODE,
        )
    except HTTPException:
        raise
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        METRICS.add(ChatCall(time.time(), len(payload.prompt), 0, latency_ms, payload.model, False, estimate_tokens(payload.prompt), 0, 0.0, str(exc)))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "simulation_mode": SIMULATION_MODE}


@app.get("/metrics", dependencies=[Depends(require_api_key)])
async def metrics() -> dict:
    return METRICS.summary()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
