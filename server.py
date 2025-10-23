from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from lang import agent_executor
from fastapi.middleware.cors import CORSMiddleware


import redis
import json
import os

# Redis setup using environment variables
# Set REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_SSL in your environment as needed
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_SSL = os.environ.get("REDIS_SSL", "false").lower() == "true"

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=REDIS_SSL,
    decode_responses=True
)

# Test Redis connection
try:
    redis_client.ping()
    print(f"[Redis] Connected successfully to {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"[Redis] Connection failed: {e}")

app = FastAPI()

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    try:
        # Retrieve user context from Redis
        history_json = redis_client.get(f"chat_history:{request.user_id}")
        if history_json:
            history = json.loads(history_json)
        else:
            history = []

        # Prepare input for agent_executor with user-specific context
        agent_input = {"input": request.input, "chat_history": history}
        # Run blocking agent_executor.invoke in a thread pool
        response = await run_in_threadpool(agent_executor.invoke, agent_input)

        # Parse response to check if it's a structured response with action_type
        output = response["output"]
        action_type = "chat"  # Default action type for regular chat
        
        # Import the normalization function from lang.py
        from lang import normalize_agent_response
        
        try:
            # Normalize the response to handle markdown fences and ensure consistency
            normalized_response = normalize_agent_response(output)
            
            # If we got a normalized response, use it
            if isinstance(normalized_response, dict) and "action_type" in normalized_response:
                action_type = normalized_response["action_type"]
                output = json.dumps(normalized_response)  # Convert back to JSON string
            else:
                # Try to parse as JSON to check for action_type
                parsed_response = json.loads(output)
                if isinstance(parsed_response, dict) and "action_type" in parsed_response:
                    action_type = parsed_response["action_type"]
        except (json.JSONDecodeError, TypeError):
            # Not a JSON response, treat as regular chat
            pass

        # Update user context in Redis (LangChain expects role/content format)
        history.extend([
            {"role": "user", "content": request.input},
            {"role": "assistant", "content": output}
        ])
        redis_client.set(f"chat_history:{request.user_id}", json.dumps(history))

        return {
            "output": output,
            "action_type": action_type
        }
    except Exception as e:
        return {"error": str(e), "action_type": "error"}

@app.get("/")
def root():
    return {"message": "Server is running. 💀💀GREEN FLAG💀💀 Watchya back"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
