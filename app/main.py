from fastapi import FastAPI
from pydantic import BaseModel
from app.api.workflow import run_workflow  
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow_id: str
    input_path: str
    output_path: str

@app.post("/workflow/start")
async def start_workflow(req: WorkflowRequest):
    results = await run_workflow(
        req.workflow_id,
        req.input_path,
        req.output_path,
    )
    return {
        "workflow_id": req.workflow_id,
        "results": results,
    }

@app.get("/")
def root():
    return {"msg": "Multi-Agent Workflow API is running!"}
