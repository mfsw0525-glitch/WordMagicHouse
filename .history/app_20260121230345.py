# app.py
import streamlit as st
import pandas as pd
from db_manager import get_stats, import_from_excel, get_random_new_words

# ==========================================
# 1. 页面配置与 CSS 美化
# ==========================================
st.set_page_config(page_title="单词魔法屋", page_icon="🏰", layout="centered")

# 自定义 CSS (多巴胺配色 + 卡通字体)
st.markdown("""
<style>
    /* 全局背景色 */
    .stApp {
        background-color: #F0F8FF;
    }
    /* 标题样式 */
    h1 {
        color: #FF69B4; /* 亮粉色 */
        font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
        text-align: center;
        text-shadow: 2px 2px #FFD700;
    }
    /* 按钮样式 */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        font-size: 20px;
        font-weight: bold;
        border: 2px solid #fff;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    /* 数据统计卡片 */
    .metric-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #87CEEB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏：家长控制台 (Admin)
# ==========================================
with st.sidebar:
    st.header("👨‍👩‍👧 家长控制台")
    st.write("上传新单词 (Excel格式)")
    uploaded_file = st.file_uploader("选择 Excel 文件", type=['xlsx'])
    
    if uploaded_file is not None:
        if st.button("开始导入"):
            success, msg = import_from_excel(uploaded_file)
            if success:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)
    
    st.info("Excel 提示: 第一行必须包含 'word' 和 'definition' 两列。")

# ==========================================
# 3. 主界面逻辑
# ==========================================

st.title("🏰 Word Magic House")
st.markdown("---")

# 获取当前数据统计
total_words, new_words_count = get_stats()

# 显示可爱的欢迎语和统计
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>📚 魔法书总单词</h3>
        <h2>{total_words}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🌱 等你来探索</h3>
        <h2>{new_words_count}</h2>
    </div>
    """, unsafe_allow_html=True)

st.write("") # 空行占位
st.write("") 

# ==========================================
# 4. 核心功能入口
# ==========================================

# 检查 Session State (用于页面跳转状态管理)
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page == 'home':
    c1, c2 = st.columns([1, 1])
    
    with c1:
        # 学习新词入口
        if st.button("🚀 开始学习 (Start New)"):
            # 获取一组随机新词
            words_to_learn = get_random_new_words(limit=20)
            if not words_to_learn:
                st.warning("哇！所有的单词都学完啦！快让爸爸导入新单词吧！")
            else:
                st.session_state.learning_queue = words_to_learn
                st.session_state.page = 'learning'
                st.rerun()

    with c2:
        # 复习入口 (后续完善逻辑)
        if st.button("🧠 复习旧词 (Review)"):
            st.info("复习功能正在建设中...")

# 简单的学习页面占位 (Step 3 会详细实现这里)
elif st.session_state.page == 'learning':
    st.subheader("🔥 正在挑战 20 个新单词")
    st.write(f"当前队列剩余: {len(st.session_state.learning_queue)} 个")
    
    if st.button("⬅️ 返回主页"):
        st.session_state.page = 'home'
        st.rerun()