import socket
import json
import io
import secrets
from fastapi import FastAPI, Request, Depends, HTTPException, Response
import qrcode
from clipboard import Clipbaord

app = FastAPI(title="Clippy")
clippy = Clipbaord()

TOKEN = secrets.token_urlsafe(32)
LOCALHOSTS = {"127.0.0.1", "::1"}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def get_token(request: Request) -> str:
    return request.headers.get("access-token", "")

@app.post("/clip")
async def recieve_clip(request: Request, token: str = Depends(get_token)):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail="Bad Token")
    
    content_type = request.headers.get("content-type", "")
    body: bytes = await request.body()

    print(f"Content Type: {content_type}")
    if content_type == "text/plain":
        clippy.set_text(body.decode())
    else:
        clippy.set_image(body)

@app.get("/pair")
async def pair(request: Request):
    if request.client is None or request.client.host not in LOCALHOSTS:
        raise HTTPException(status_code=403, detail="Pairing is only available from this computer")
    payload = json.dumps({
        "host": get_local_ip(),
        "port": 8000,
        "token": TOKEN
    })
    print(get_local_ip())
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png")
