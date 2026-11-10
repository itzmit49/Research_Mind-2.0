import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents import research_graph

app = FastAPI(
    title="ResearchMind API",
    description="FastAPI Backend powered by LangGraph",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str


@app.get("/")
def root():
    return {
        "message": (
            "ResearchMind API is running. "
            "Use POST /api/research to run the LangGraph pipeline."
        )
    }


@app.post("/api/research")
def run_research(req: ResearchRequest):
    topic_val = req.topic.strip()

    if not topic_val:
        raise HTTPException(
            status_code=400,
            detail="Research topic cannot be empty.",
        )

    initial_state = {
        "topic": topic_val,
        "search_results": [],
        "documents": [],
        "research": "",
        "report": "",
        "critic_feedback": "",
        "critic_score": 0.0,
        "retrieval_attempts": 0,
        "revision_count": 0,
    }

    try:
        result = research_graph.invoke(initial_state)

        return {
            "search": "\n\n".join(result.get("search_results", [])),
            "reader": "\n\n".join(result.get("documents", [])),
            "writer": result.get("report", ""),
            "critic": result.get("critic_feedback", ""),
            "critic_score": result.get("critic_score", 0.0),
        }

    except Exception as e:
        print(f"Research pipeline failed: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline execution failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
