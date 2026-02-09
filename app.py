# app.py
import streamlit as st
import random
import time
import pandas as pd
from db_manager import get_stats, import_from_excel, get_random_new_words, update_word_mastery

# ==========================================
# 1. 核心配置与 "魔法皮肤" (CSS)
# ==========================================
st.set_page_config(page_title="Word Magic House", page_icon="🏰", layout="centered")

# 这里的 CSS 是关键，它会覆盖 Streamlit 原生的丑样式
st.markdown("""
<style>
    /* --- 全局背景：梦幻渐变 --- */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); /* 默认柔和背景 */
        background-image: linear-gradient(to top, #a18cd1 0%, #fbc2eb 100%); /* 魔法紫粉色 */
    }
    
    /* --- 标题文字：卡通风 --- */
    h1 {
        color: #FFFFFF;
        font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
        text-shadow: 3px 3px 0px #9daaf2;
        font-size: 3rem !important;
        text-align: center;
        padding-bottom: 20px;
    }
    
    /* --- 数据卡片 (Glassmorphism 毛玻璃效果) --- */
    .metric-card {
        background: rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    .metric-value { font-size: 2.5rem; font-weight: bold; }
    .metric-label { font-size: 1.2rem; opacity: 0.9; }

    /* --- 释义大卡片 --- */
    .def-card {
        background-color: #ffffff;
        border-radius: 25px;
        padding: 40px 20px;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 6px solid #FFB7B2; /* 底部装饰线 */
        font-size: 26px;
        color: #4A4A4A;
        font-weight: bold;
    }

    /* --- 按钮大改造 (3D 游戏风格) --- */
    .stButton > button {
        width: 100%;
        height: 75px;
        border-radius: 20px;
        border: none;
        color: white;
        font-size: 22px !important;
        font-weight: 800;
        letter-spacing: 1px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        background: linear-gradient(to bottom, #FF9A9E 0%, #FECFEF 100%); /* 默认粉色 */
        box-shadow: 0px 6px 0px #E0787E, 0px 6px 15px rgba(0,0,0,0.2); /* 3D阴影 */
        transition: all 0.1s;
        margin-bottom: 10px;
    }
    
    /* 按钮按下效果 */
    .stButton > button:active {
        transform: translateY(4px);
        box-shadow: 0px 2px 0px #E0787E;
    }
    
    /* 给不同功能的按钮“染色” (Streamlit 不好给单个按钮加ID，这里利用层级) */
    /* 我们可以通过 Python 逻辑尽量保持按钮风格一致 */

    /* --- 输入框美化 --- */
    .stTextInput > div > div > input {
        border-radius: 15px;
        height: 60px;
        font-size: 24px;
        text-align: center;
        border: 3px solid #A18CD1;
        color: #555;
    }

    /* --- 提示文字 --- */
    .hint-box {
        background-color: #FFEFD5;
        color: #FF8C00;
        padding: 10px;
        border-radius: 15px;
        text-align: center;
        font-family: monospace;
        font-size: 28px;
        letter-spacing: 6px;
        margin-bottom: 20px;
        border: 2px dashed #FFD700;
    }
    
    /* 隐藏默认的汉堡菜单和页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 逻辑函数
# ==========================================

def generate_spelling_hint(word):
    length = len(word)
    # 30% 概率给 Hard 模式 (全空)
    if length <= 3 or random.random() < 0.3:
        return "_ " * length
    
    # Easy 模式：给 1 到 50% 的字母
    max_reveal = max(1, int(length / 2))
    num_to_reveal = random.randint(1, max_reveal)
    indices = set(random.sample(range(length), num_to_reveal))
    
    chars = []
    for i in range(length):
        if i in indices:
            chars.append(word[i])
        else:
            chars.append("_")
    return " ".join(chars)

def init_learning_session(words):
    st.session_state.learning_queue = words
    st.session_state.progress_map = {w['id']: 0 for w in words}
    st.session_state.matching_batch = []
    st.session_state.selected_word_id = None
    if 'current_spelling_word' in st.session_state:
        del st.session_state['current_spelling_word']

def check_matching(word_id):
    # 如果还没选第一个词
    if st.session_state.selected_word_id is None:
        st.session_state.selected_word_id = word_id
        return

    # 如果选了同一个词（取消选择）
    if st.session_state.selected_word_id == word_id:
        st.session_state.selected_word_id = None
        return
    
    # 选中了第二个词，开始对比
    if st.session_state.selected_word_id == word_id: # ID相同，配对成功
        # 注意：这里逻辑其实已经在上面覆盖了。
        # 真实的配对逻辑是：左边点了词A，右边点了义A。
        # 但我们的数据结构里，词和义共用一个 word_id。
        # 所以只要判断两次点击传递进来的 word_id 是否一致即可。
        pass 
        
    # 由于Streamlit的机制，我们得在按钮点击时直接判断
    # 这一块逻辑放在UI渲染部分处理更顺畅
    pass

# ==========================================
# 3. 页面主程序
# ==========================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- 🏠 主页 HOME ---
if st.session_state.page == 'home':
    st.title("🏰 Word Magic Castle")
    
    total, new_cnt, review_cnt, learned_cnt = get_stats()
    
    # 漂亮的磨砂玻璃数据卡片
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total}</div>
            <div class="metric-label">📚 单词总数</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{new_cnt}</div>
            <div class="metric-label">🌟 待学新词</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacer

    col1, col2 = st.columns(2)
    with col1:
        # Start 按钮
        if st.button("🚀 出发去学习\nStart", use_container_width=True):
            words = get_random_new_words(20)
            if not words:
                st.warning("太厉害了！所有单词都学会啦！")
            else:
                init_learning_session(words)
                st.session_state.page = 'learning_matching'
                st.rerun()
                
    with col2:
        # Review 按钮
        if st.button("🧠 记忆复习\nReview", use_container_width=True):
            st.info("🚧 正在施工中...")

    # 家长控制台 (侧边栏)
    with st.sidebar:
        st.write("🔧 **家长通道**")
        up = st.file_uploader("上传单词Excel", type=['xlsx'])
        if up and st.button("导入"):
            ok, msg = import_from_excel(up)
            if ok: st.success(msg)
            else: st.error(msg)

# --- 🧩 游戏 1: 连连看 (Matching) ---
elif st.session_state.page == 'learning_matching':
    st.markdown("<h1>🧩 魔法连连看</h1>", unsafe_allow_html=True)
    
    # 筛选未通过配对的词
    need_matching = [w for w in st.session_state.learning_queue if st.session_state.progress_map[w['id']] < 1]
    
    if len(need_matching) == 0:
        st.session_state.page = 'learning_spelling'
        st.rerun()
    
    # 补货
    current_ids = [w['id'] for w in st.session_state.matching_batch]
    st.session_state.matching_batch = [w for w in st.session_state.matching_batch if st.session_state.progress_map[w['id']] < 1]
    while len(st.session_state.matching_batch) < 4 and len(need_matching) > len(st.session_state.matching_batch):
        candidates = [w for w in need_matching if w not in st.session_state.matching_batch]
        if not candidates: break
        st.session_state.matching_batch.append(random.choice(candidates))
        
    batch = st.session_state.matching_batch
    
    # --- 渲染游戏区 ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<h3 style='text-align:center; color:white;'>🔤 英文</h3>", unsafe_allow_html=True)
        for w in batch:
            # 动态改变按钮文本，显示选中状态
            label = w['word']
            if st.session_state.selected_word_id == w['id']:
                label = f"✨ {label} ✨"
                
            if st.button(label, key=f"left_{w['id']}", use_container_width=True):
                st.session_state.selected_word_id = w['id']
                st.rerun() # 刷新以显示选中特效
                
    with c2:
        st.markdown("<h3 style='text-align:center; color:white;'>📖 中文</h3>", unsafe_allow_html=True)
        # 乱序显示中文
        shuffled = sorted(batch, key=lambda x: x['definition']) 
        for w in shuffled:
            if st.button(w['definition'], key=f"right_{w['id']}", use_container_width=True):
                # 配对逻辑判断
                if st.session_state.selected_word_id == w['id']:
                    st.success("Bingo! 🎉")
                    st.session_state.progress_map[w['id']] += 1
                    st.session_state.selected_word_id = None
                    time.sleep(0.5)
                    st.rerun()
                else:
                    if st.session_state.selected_word_id is not None:
                        st.error("不匹配哦，再试试 😅")
                        st.session_state.progress_map[st.session_state.selected_word_id] = 0
                        st.session_state.progress_map[w['id']] = 0
                        st.session_state.selected_word_id = None
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("👈 请先点击左边的单词")

    st.write("---")
    if st.button("⏩ 跳过 (Dev Only)"):
        st.session_state.page = 'learning_spelling'
        st.rerun()

# --- ✍️ 游戏 2: 拼写 (Spelling) ---
elif st.session_state.page == 'learning_spelling':
    st.markdown("<h1>✍️ 单词拼写</h1>", unsafe_allow_html=True)
    
    remaining = [w for w in st.session_state.learning_queue if st.session_state.progress_map[w['id']] < 2]
    
    if not remaining:
        st.balloons()
        st.markdown("""
        <div class="def-card" style="border-bottom: 6px solid #98FB98;">
            🌟 任务完成！所有单词都掌握了！
        </div>
        """, unsafe_allow_html=True)
        # 写入数据库
        for w in st.session_state.learning_queue:
            update_word_mastery(w['id'], True)
            
        if st.button("🏠 回家"):
            st.session_state.page = 'home'
            st.rerun()
        st.stop()
        
    # 选词
    if 'current_spelling_word' not in st.session_state:
        st.session_state.current_spelling_word = random.choice(remaining)
        st.session_state.spelling_attempt = 0
        st.session_state.current_hint = generate_spelling_hint(st.session_state.current_spelling_word['word'])
    
    target = st.session_state.current_spelling_word
    
    # 释义卡片
    st.markdown(f"""
    <div class="def-card">
        {target['definition']}
    </div>
    """, unsafe_allow_html=True)
    
    # 提示框
    st.markdown(f'<div class="hint-box">{st.session_state.current_hint}</div>', unsafe_allow_html=True)
    
    # 输入区域
    # 为了让输入框好看，我们在 CSS 里定制了 .stTextInput
    user_input = st.text_input("", placeholder="在此输入单词...", key="sp_input").strip()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("✨ 确定 ✨", use_container_width=True):
            if user_input.lower() == target['word'].lower():
                st.success("太棒了！拼对了！🎉")
                time.sleep(0.8)
                
                if st.session_state.spelling_attempt == 0:
                    st.session_state.progress_map[target['id']] = 2
                else:
                    st.session_state.progress_map[target['id']] += 1
                
                del st.session_state['current_spelling_word']
                st.rerun()
            else:
                st.error(f"哎呀，不对哦。正确是: {target['word']}")
                st.session_state.spelling_attempt += 1
                st.session_state.progress_map[target['id']] = 0
                st.info("💡 只有完全拼对一次才能过关哦")
    
    with c2:
        if st.session_state.spelling_attempt > 0:
            if st.button("➡️ 下一个"):
                del st.session_state['current_spelling_word']
                st.rerun()

    # 底部进度
    progress = 1 - (len(remaining) / 20)
    st.progress(progress)