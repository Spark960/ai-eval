from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uuid
import asyncio
import httpx
import json
import threading
from eval_runner import run_evaluation_thread

app = FastAPI()

# Enable CORS for the Vite frontend (port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state management
queues = {}
results_store = {}

@app.post("/api/evaluate")
async def start_eval(request: Request):
    data = await request.json()
    run_id = str(uuid.uuid4())
    
    queues[run_id] = asyncio.Queue()
    results_store[run_id] = {"status": "running"}
    
    # Spawn the background thread
    loop = asyncio.get_running_loop()
    threading.Thread(
        target=run_evaluation_thread,
        args=(run_id, data['model'], data['api_key'], queues[run_id], loop, results_store),
        daemon=True
    ).start()
    
    return {"run_id": run_id}

@app.get("/api/stream/{run_id}")
async def stream_logs(run_id: str):
    async def event_generator():
        queue = queues.get(run_id)
        if not queue:
            yield f"data: {json.dumps({'error': 'Invalid run_id'})}\n\n"
            return
        
        while True:
            msg = await queue.get()
            if msg == "[EVAL_DONE]":
                final_data = results_store.get(run_id, {})
                yield f"data: {json.dumps({'done': True, 'results': final_data.get('data')})}\n\n"
                break
            elif msg.startswith("[EVAL_ERROR]"):
                yield f"data: {json.dumps({'error': msg})}\n\n"
                break
            else:
                yield f"data: {json.dumps({'log': msg})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# THE ELEGANT FIX: Native FastAPI Proxy to strip the 'seed' parameter
@app.post("/proxy/v1/chat/completions")
async def gemini_proxy(request: Request):
    payload = await request.json()
    
    payload.pop('seed', None)
    payload.pop('presence_penalty', None)
    payload.pop('frequency_penalty', None)
    
    auth_header = request.headers.get('Authorization')
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url, 
            json=payload, 
            headers={'Authorization': auth_header},
            timeout=60.0
        )
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")