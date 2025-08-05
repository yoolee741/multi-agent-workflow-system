from fastapi import FastAPI
from pydantic import BaseModel
from app.api.workflow import run_workflow  
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class WorkflowRequest(BaseModel):
    user_name: str

@app.post("/workflow/start")
async def start_workflow(req: WorkflowRequest):
    result = await run_workflow(
        req.user_name,
    )
    return {
        "workflow_id": result["workflow_id"],
        "results": result["results"],
    }

@app.get("/")
def root():
    return {"msg": "Multi-Agent Workflow API is running!"}
