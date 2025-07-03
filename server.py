from fastapi import FastAPI, Request
from pydantic import BaseModel
from lang import agent_executor

app = FastAPI()

class QueryRequest(BaseModel):
    input: str

@app.post("/query")
async def query(request: QueryRequest):
    response = agent_executor.invoke({"input": request.input})
    return {"output": response["output"]}

@app.get("/")
def root():
    return {"message": "Agent Executor API is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
