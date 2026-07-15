from fastapi import APIRouter
from pydantic import BaseModel
from src.agents.research_agent import ResearchAgent
from src.memory.memory_manager import RedisMemory

router = APIRouter()
agent = ResearchAgent()
memory = RedisMemory()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    cached = memory.get_cache(req.query)
    if cached: return {"answer": cached, "source": "Redis Memory", "contexts": []}
    
    result = agent.process_query(req.query)
    
    memory.set_cache(req.query, result["answer"])
    return {"answer": result["answer"], "source": "Research Agent", "contexts": result.get("contexts", [])}