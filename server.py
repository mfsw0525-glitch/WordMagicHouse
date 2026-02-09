# server.py
import os
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from io import BytesIO
from db_manager import get_stats, get_random_new_words, get_words_for_review, update_word_mastery, import_from_excel, get_learned_words_details

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

@app.get("/api/stats")
async def api_stats():
    total, new_cnt, review_cnt, learned_cnt = get_stats()
    return {
        "total": total, 
        "new_words": new_cnt, 
        "review_count": review_cnt,
        "learned_count": learned_cnt  # 🆕 新增已学数量
    }

@app.get("/api/new_words")
async def api_new_words():
    return get_random_new_words(20)

@app.get("/api/review_words")
async def api_review_words():
    return get_words_for_review(30)

# 🆕 获取已学单词详情列表
@app.get("/api/learned_detail")
async def api_learned_detail():
    return get_learned_words_details()

@app.post("/api/update_progress")
async def api_update_progress(data: ProgressUpdate):
    update_word_mastery(data.word_id, data.success)
    return {"status": "ok"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    file_obj = BytesIO(content)
    success, message = import_from_excel(file_obj)
    return {"success": success, "message": message}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)