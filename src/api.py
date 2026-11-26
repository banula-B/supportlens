from contextlib import asynccontextmanager
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from pydantic import BaseModel, Field, field_validator

from answer_generator import Answer
from service import SupportLensService


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def reject_blank_question(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be blank.")

        return value


class Source(BaseModel):
    id: str
    title: str
    source: str


class AskResponse(BaseModel):
    withheld: bool
    answer: Answer | None
    verification_status: Literal[
        "supported",
        "unsupported",
        "uncertain",
        "not_checked",
    ]
    sources: list[Source]


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = SupportLensService()
    app.state.service = service
    app.state.ask_lock = Lock()

    try:
        yield
    finally:
        service.close()


app = FastAPI(
    title="SupportLens API",
    description="Technical support answers from retrieved evidence.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    # This checks the local application, not Groq availability.
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request):
    lock = request.app.state.ask_lock

    # Limit this local prototype to one active question at a time.
    if not lock.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail="SupportLens is processing another question.",
        )

    try:
        result = request.app.state.service.ask(payload.question)

        verification_status = (
            result.verification.verdict
            if result.verification is not None
            else "not_checked"
        )

        return AskResponse(
            withheld=result.withheld,
            answer=result.answer,
            verification_status=verification_status,
            sources=[
                Source(**source) for source in result.sources
            ],
        )

    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="The model provider's request quota was exceeded.",
        ) from None

    except APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="The model provider did not respond in time.",
        ) from None

    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to the model provider.",
        ) from None

    except APIStatusError:
        raise HTTPException(
            status_code=502,
            detail="The model provider returned an error.",
        ) from None

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="The generated response failed validation.",
        ) from None

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An internal processing error occurred.",
        ) from None

    finally:
        lock.release()