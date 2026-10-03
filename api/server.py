from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os
import json
import yaml
import httpx

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / 'config'

app = FastAPI(title='Draeven Jarvis API', version='1.0.0')


def load_yaml(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


jarvis_config = load_yaml(CONFIG_DIR / 'jarvis-config.yaml')
llm_routing = load_yaml(CONFIG_DIR / 'llm-routing.yaml')


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    task_type: str | None = None


class ChatResponse(BaseModel):
    reply: str
    provider: str
    session_id: str | None = None


@app.get('/health')
def health():
    return {"status": "ok", "app": jarvis_config.get('app_name', 'Draeven Jarvis')}


@app.post('/api/chat', response_model=ChatResponse)
async def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        return ChatResponse(reply='No message was provided.', provider='local', session_id=request.session_id)

    provider = pick_provider(request.task_type or 'general', message)
    reply = await route_to_provider(provider, message)

    return ChatResponse(reply=reply, provider=provider, session_id=request.session_id)


@app.post('/api/route')
async def route_only(request: ChatRequest):
    provider = pick_provider(request.task_type or 'general', request.message)
    return {"provider": provider, "message": request.message}


def pick_provider(task_type: str, message: str) -> str:
    # Simple deterministic router for simplicity.
    task = (task_type or 'general').lower()
    text = message.lower()

    if 'code' in text or 'script' in text or 'api' in text or task == 'coding':
        return 'openai'
    if 'design' in text or 'marketing' in text or 'creative' in text or 'packaging' in text or task == 'creative':
        return 'gemini'
    if 'document' in text or 'essay' in text or 'analyze' in text or 'large' in text or task == 'analysis':
        return 'claude'
    return 'ollama'


async def route_to_provider(provider: str, message: str) -> str:
    if provider == 'ollama':
        return await call_ollama(message)
    if provider == 'openai':
        return await call_openai(message)
    if provider == 'claude':
        return await call_claude(message)
    if provider == 'gemini':
        return await call_gemini(message)
    return 'No valid provider selected.'


async def call_ollama(prompt: str) -> str:
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = os.getenv('OLLAMA_MODEL', 'llama3.1')

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f'{base_url}/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False
                }
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get('response', 'No response from Ollama.')
    except Exception as exc:
        return (
            'Ollama is not available locally. '
            'Install Ollama and start a local model, or add a cloud API key in .env. '
            f'Error: {exc}'
        )


async def call_openai(prompt: str) -> str:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return 'OPENAI_API_KEY is not configured. Add your key in .env.'

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f'OpenAI call failed: {exc}'


async def call_claude(prompt: str) -> str:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return 'ANTHROPIC_API_KEY is not configured. Add your key in .env.'

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}],
        )
        text = response.content
        if isinstance(text, list):
            return ''.join(part.text for part in text if getattr(part, 'text', None))
        return str(text)
    except Exception as exc:
        return f'Claude call failed: {exc}'


async def call_gemini(prompt: str) -> str:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return 'GOOGLE_API_KEY is not configured. Add your key in .env.'

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.5-pro'))
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        return f'Gemini call failed: {exc}'


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'api.server:app',
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '8000')),
        reload=False,
    )
