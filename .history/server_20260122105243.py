# server.py
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from db_manager import get_stats, get_random_new_words, get_words_for_review, update_word_mastery

app = FastAPI()

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProgressUpdate(BaseModel):
    word_id: int
    success: bool

@app.get("/")
async def read_root():
    return FileResponse("templates/index.html")

# 📊 统计接口：现在返回 review_count
@app.get("/api/stats")
async def api_stats():
    total, new_cnt, review_cnt = get_stats()
    return {
        "total": total, 
        "new_words": new_cnt, 
        "review_count": review_cnt
    }

# 🚀 新词接口
@app.get("/api/new_words")
async def api_new_words():
    return get_random_new_words(20)

# 🧠 复习接口 (New)
@app.get("/api/review_words")
async def api_review_words():
    # 一次最多复习 30 个，防止小朋友太累
    return get_words_for_review(30)

# ✅ 进度更新接口
@app.post("/api/update_progress")
async def api_update_progress(data: ProgressUpdate):
    update_word_mastery(data.word_id, data.success)
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)