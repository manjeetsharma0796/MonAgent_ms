

from fastapi import FastAPI, Request
from pydantic import BaseModel
from lang import agent_executor
from typing import Dict, List
from threading import Lock

# In-memory user context store (user_id -> list of messages)
user_contexts: Dict[str, List[Dict]] = {}
context_lock = Lock()

app = FastAPI()


class QueryRequest(BaseModel):
    input: str
    user_id: str

import uuid
@app.post("/start")
def start():
    """
    Generate and return a new user_id for a new user session.
    """
    user_id = str(uuid.uuid4())
    return {"user_id": user_id}

@app.post("/query")
async def query(request: QueryRequest):
    # Retrieve or create user context
    with context_lock:
        history = user_contexts.get(request.user_id, [])

    # Prepare input for agent_executor with user-specific context
    agent_input = {"input": request.input, "chat_history": history}
    response = agent_executor.invoke(agent_input)

    # Update user context with new message and response (LangChain expects role/content format)
    with context_lock:
        user_contexts.setdefault(request.user_id, []).extend([
            {"role": "user", "content": request.input},
            {"role": "assistant", "content": response["output"]}
        ])

    return {"output": response["output"]}

@app.get("/")
def root():
    return {"message": "Agent Executor API is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
