from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .config import settings
from .db import db
from .schemas import ChatRequest, ChatResponse, ProfileResponse
from .service import chat

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="具备情绪识别、长期记忆、关系养成与安全边界的 AI 情感陪伴智能体 MVP。",
)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        return await chat(request.user_id, request.session_id, request.message, request.device_context)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"服务处理失败：{exc}") from exc


@app.get("/v1/profile/{user_id}", response_model=ProfileResponse)
def profile_endpoint(user_id: str):
    try:
        return db.get_profile(user_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取画像失败：{exc}") from exc


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>SoulPal</title>
<style>body{font-family:system-ui;max-width:760px;margin:40px auto;padding:0 16px;background:#f5f5f7}.card{background:white;border-radius:18px;padding:22px;box-shadow:0 8px 30px #0001}#log{min-height:320px;max-height:480px;overflow:auto;padding:12px;background:#fafafa;border-radius:12px}.msg{margin:10px 0;padding:10px 14px;border-radius:12px;white-space:pre-wrap}.user{background:#e8f0ff;margin-left:18%}.bot{background:#fff0f3;margin-right:18%}.row{display:flex;gap:10px;margin-top:14px}input{flex:1;padding:13px;border:1px solid #ddd;border-radius:12px;font-size:16px}button{padding:0 18px;border:0;border-radius:12px;cursor:pointer}</style></head>
<body><div class="card"><h2>小栖 · AI 情感陪伴智能体</h2><div id="log"></div><div class="row"><input id="input" placeholder="和小栖说点什么……"/><button onclick="send()">发送</button></div></div>
<script>const userId=localStorage.getItem('soulpal_user')||crypto.randomUUID(),sessionId=crypto.randomUUID();localStorage.setItem('soulpal_user',userId);const log=document.getElementById('log'),input=document.getElementById('input');function add(role,text){const el=document.createElement('div');el.className='msg '+role;el.textContent=text;log.appendChild(el);log.scrollTop=log.scrollHeight}async function send(){const message=input.value.trim();if(!message)return;input.value='';add('user',message);try{const res=await fetch('/v1/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,session_id:sessionId,message,device_context:{scene:'web_demo'}})});const data=await res.json();if(!res.ok)throw new Error(data.detail||'请求失败');add('bot',data.reply+'\n\n[情绪：'+data.emotion.label+'｜亲密度：'+data.companion_state.intimacy+']')}catch(e){add('bot','连接失败：'+e.message)}}input.addEventListener('keydown',e=>{if(e.key==='Enter')send()});add('bot','我在这儿。今天想从哪里聊起？');</script></body></html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
