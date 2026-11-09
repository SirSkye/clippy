from fastapi import FastAPI, Request
from clipboard import Clipbaord

app = FastAPI(title="Clippy")
clippy = Clipbaord()

@app.post("/clip")
async def recieve_clip(request: Request):
    content_type = request.headers.get("content-type", "")
    body: bytes = await request.body()

    print(f"Content Type: {content_type}")
    if content_type == "text/plain":
        clippy.set_text(body.decode())
    else:
        clippy.set_image(body)
