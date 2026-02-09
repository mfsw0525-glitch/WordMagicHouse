# server.py
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 引入数据库管理模块
# 确保 db_manager.py 在同一目录下
from db_manager import get_stats, get_random_new_words, update_word_mastery

# 创建 FastAPI 实例
app = FastAPI()

# ==========================================
# 1. 静态文件配置 (关键修复)
# ==========================================
# 自动创建 static 文件夹（如果不存在），防止报错
if not os.path.exists("static"):
    os.makedirs("static")

# 将 /static 路径挂载到 static 文件夹
# 这样前端 index.html 以后就可以通过 /static/icon.png 访问图片了
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 2. 模板配置
# ==========================================
# 指向 templates 文件夹，index.html 放在这里
templates = Jinja2Templates(directory="templates")

# ==========================================
# 3. 数据模型 (Pydantic)
# ==========================================
# 用于接收前端传来的学习进度数据
class ProgressUpdate(BaseModel):
    word_id: int
    success: bool

# ==========================================
# 4. API 路由接口
# ==========================================

# 🏠 首页入口
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 渲染 index.html 返回给浏览器
    return templates.TemplateResponse("index.html", {"request": request})

# 📊 获取统计数据接口
@app.get("/api/stats")
async def api_stats():
    total, new_cnt = get_stats()
    return {"total": total, "new_words": new_cnt}

# 🚀 获取一组随机新单词接口 (20个)
@app.get("/api/new_words")
async def api_new_words():
    words = get_random_new_words(20)
    return words

# ✅ 更新学习进度接口
@app.post("/api/update_progress")
async def api_update_progress(data: ProgressUpdate):
    # 调用 db_manager 更新数据库
    update_word_mastery(data.word_id, data.success)
    return {"status": "ok"}

# ==========================================
# 5. 启动入口
# ==========================================
if __name__ == "__main__":
    # host="0.0.0.0" 允许局域网设备（如 iPad）访问
    # port=8000 是端口号
    # reload=True 表示修改代码后自动重启，方便调试
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)