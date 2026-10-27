import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from app.agents.devops_agent import devops_agent
from app.llm.client import close_model_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_model_client()


app = FastAPI(
    title="Agentic Infrastructure Operations Platform",
    lifespan=lifespan,
)
logger = logging.getLogger(__name__)


class UserRequest(BaseModel):
    request: str


@app.get("/")
def root():
    return {
        "message": "Agentic Infrastructure Operations Platform is running"
    }


@app.post("/agent")
async def agent_gateway(user_request: UserRequest):

    request = user_request.request

    try:
        result = await devops_agent(request)

        response_body = {
            "received_request": request,
            "routing_result": result
        }
        if result.get("status") == "needs_input":
            return JSONResponse(status_code=422, content=response_body)
        return response_body

    except Exception:
        logger.exception("Agent request failed")
        raise HTTPException(
            status_code=502,
            detail={
                "status": "failed",
                "message": (
                    "The request could not be completed due to "
                    "an error in an agent or external service."
                )
            }
        )
