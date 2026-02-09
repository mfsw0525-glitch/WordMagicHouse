# server.py
import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse  # 关键修改：引入文件响应
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 引入数据库管理模块
from db_manager import get_stats, get_random_new_words, update_word_mastery

app = FastAPI()

# ==========================================
# 1. 静态文件配置
# ==========================================
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 2. 数据模型
# ==========================================
class ProgressUpdate(BaseModel):
    word_id: int
    success: bool

# ==========================================
# 3. API 路由接口
# ==========================================

# 🏠 首页入口 (关键修改点！)
@app.get("/")
async def read_root():
    # 以前是用 templates.TemplateResponse，它会解析 {{ }} 导致报错
    # 现在改用 FileResponse，直接把 HTML 文件发给浏览器，不解析
    return FileResponse("templates/index.html")

# 📊 获取统计数据接口
@app.get("/api/stats")
async def api_stats():
    total, new_cnt = get_stats()
    return {"total": total, "new_words": new_cnt}

# 🚀 获取一组随机新单词接口
@app.get("/api/new_words")
async def api_new_words():
    words = get_random_new_words(20)
    return words

# ✅ 更新学习进度接口
@app.post("/api/update_progress")
async def api_update_progress(data: ProgressUpdate):
    update_word_mastery(data.word_id, data.success)
    return {"status": "ok"}

# ==========================================
# 4. 启动入口
# ==========================================
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)