"""CryptoLab BB84 Chat API (Refactored).

Run locally with:

    uvicorn chat_refactored:app --reload --port 8000

Environment variables:

    CHAT_API_KEY              Optional shared secret. Defaults to "dev-chat-key".
    CHAT_SIMULATION_MODE      "true" by default. Set to "false" for real OpenAI calls.
    SIMULATED_LATENCY_MS      Artificial simulation latency, default 250.
    OPENAI_API_KEY            Required only when CHAT_SIMULATION_MODE=false.

This refactored version improves error handling, separates concerns, and adds
better type safety and configuration management.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from enum import Enum
from statistics import quantiles
from typing import AsyncGenerator, Deque

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator


class SimulationMode(str, Enum):
    """Simulation mode configuration."""
    ENABLED = "true"
    DISABLED = "false"


@dataclass(frozen=True)
class ChatConfig:
    """Configuration for the chat API."""
    api_key: str = os.getenv("CHAT_API_KEY", "dev-chat-key")
    simulation_mode: bool = os.getenv("CHAT_SIMULATION_MODE", "true").lower() != "false"
    simulated_latency_ms: int = int(os.getenv("SIMULATED_LATENCY_MS", "250"))
    rate_limit_per_second: int = 10
    max_prompt_length: int = 8000
    
    def __post_init__(self):
        """Validate configuration."""
        if self.simulated_latency_ms < 0:
            raise ValueError("SIMULATED_LATENCY_MS must be non-negative")
        if self.rate_limit_per_second < 1:
            raise ValueError("Rate limit must be at least 1")


CONFIG = ChatConfig()


@dataclass
class ChatCall:
    """Record of a single chat API call."""
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
        """Add a call record to metrics."""
        self.calls.append(call)

    def summary(self) -> dict:
        """Generate summary statistics from collected calls."""
        calls = list(self.calls)
        if not calls:
            return {
                "total_calls": 0,
                "p95_latency_ms": 0.0,
                "error_rate": 0.0,
                "total_estimated_cost_usd": 0.0,
                "recent": []
            }
        
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


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, limit_per_second: int = 10):
        self.limit = limit_per_second
        self.buckets: dict[str, Deque[float]] = defaultdict(deque)
    
    def check_rate_limit(self, client_id: str) -> None:
        """Check if client has exceeded rate limit."""
        now = time.time()
        bucket = self.buckets[client_id]
        
        # Remove old entries
        while bucket and now - bucket[0] > 1.0:
            bucket.popleft()
        
        if len(bucket) >= self.limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.limit} requests per second"
            )
        
        bucket.append(now)


METRICS = ChatMetrics()
RATE_LIMITER = RateLimiter(CONFIG.rate_limit_per_second)


class ChatRequest(BaseModel):
    """Request model for chat completions."""
    prompt: str = Field(..., min_length=1, max_length=8000)
    model: str = "gpt-4.1-mini"
    stream: bool = False
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt is not empty after stripping."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v


class ChatResponse(BaseModel):
    """Response model for chat completions."""
    response: str
    model: str
    latency_ms: float
    tokens_used: int
    estimated_cost_usd: float
    simulation_mode: bool


class TokenEstimator:
    """Utility for estimating token counts."""
    
    @staticmethod
    def estimate(text: str) -> int:
        """Estimate token count from text length."""
        return max(1, int(len(text) / 4))


class ChatService:
    """Service for generating chat responses."""
    
    @staticmethod
    def simulation_answer(prompt: str) -> str:
        """Generate a simulated response."""
        return (
            "CryptoLab assistant: "
            "For BB84, compare Alice and Bob's sampled sifted bits to estimate QBER. "
            "If QBER rises above the safety threshold, treat the channel as compromised. "
            f"Your question was: {prompt[:500]}"
        )
    
    @staticmethod
    async def generate_answer(prompt: str, model: str) -> str:
        """Generate an answer using configured backend."""
        if CONFIG.simulation_mode:
            await asyncio.sleep(CONFIG.simulated_latency_ms / 1000)
            return ChatService.simulation_answer(prompt)
        
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="OpenAI package not installed. Install it or enable CHAT_SIMULATION_MODE=true"
            ) from exc
        
        try:
            client = AsyncOpenAI()
            completion = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a concise BB84 quantum cryptography teaching assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content or ""
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API call failed: {str(exc)}"
            ) from exc
    
    @staticmethod
    async def stream_words(text: str) -> AsyncGenerator[str, None]:
        """Stream response word by word."""
        for word in text.split():
            yield f"data: {word}\n\n"
            await asyncio.sleep(0.035)
        yield "data: [DONE]\n\n"


# FastAPI app setup
app = FastAPI(
    title="CryptoLab BB84 Chat API",
    version="2.0.0",
    description="Refactored chat API with improved error handling and structure"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Dependency to validate API key."""
    if CONFIG.api_key and x_api_key != CONFIG.api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid X-API-Key header"
        )


async def rate_limit(request: Request) -> None:
    """Dependency to enforce rate limiting."""
    client_id = request.client.host if request.client else "unknown"
    RATE_LIMITER.check_rate_limit(client_id)


@app.post(
    "/v1/chat/completions",
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
    response_model=None
)
async def chat_completions(payload: ChatRequest):
    """Handle chat completion requests."""
    start = time.perf_counter()
    
    try:
        answer = await ChatService.generate_answer(payload.prompt, payload.model)
        latency_ms = (time.perf_counter() - start) * 1000
        
        prompt_tokens = TokenEstimator.estimate(payload.prompt)
        completion_tokens = TokenEstimator.estimate(answer)
        cost = (prompt_tokens + completion_tokens) * 0.000002
        
        METRICS.add(ChatCall(
            timestamp=time.time(),
            prompt_chars=len(payload.prompt),
            response_chars=len(answer),
            latency_ms=latency_ms,
            model=payload.model,
            success=True,
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            estimated_cost_usd=cost
        ))
        
        if payload.stream:
            return StreamingResponse(
                ChatService.stream_words(answer),
                media_type="text/event-stream"
            )
        
        return ChatResponse(
            response=answer,
            model=payload.model,
            latency_ms=round(latency_ms, 2),
            tokens_used=prompt_tokens + completion_tokens,
            estimated_cost_usd=round(cost, 6),
            simulation_mode=CONFIG.simulation_mode,
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        METRICS.add(ChatCall(
            timestamp=time.time(),
            prompt_chars=len(payload.prompt),
            response_chars=0,
            latency_ms=latency_ms,
            model=payload.model,
            success=False,
            tokens_prompt=TokenEstimator.estimate(payload.prompt),
            tokens_completion=0,
            estimated_cost_usd=0.0,
            error=str(exc)
        ))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "simulation_mode": CONFIG.simulation_mode,
        "version": "2.0.0"
    }


@app.get("/metrics", dependencies=[Depends(require_api_key)])
async def metrics() -> dict:
    """Get API metrics."""
    return METRICS.summary()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
