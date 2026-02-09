# app.py
import streamlit as st
import random
import time
from db_manager import get_stats, import_from_excel, get_random_new_words, update_word_mastery

# ==========================================
# 1. 配置与 CSS (iPad 触摸优化版 + 糖果风)
# ==========================================
st.set_page_config(page_title="单词魔法屋", page_icon="🏰", layout="centered")

st.markdown("""
<style>
    /* 全局背景：柔和的护眼蓝 */
    .stApp {
        background-color: #E6F3FF;
    }
    
    /* 标题样式：卡通可爱风 */
    h1 {
        color: #FF69B4; 
        font-family: 'Comic Sans MS', cursive, sans-serif;
        text-align: center;
        text-shadow: 2px 2px 0px #FFF;
    }
    
    /* 释义框样式：像一张大卡片 */
    .def-box {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 20px;
        border: 4px solid #87CEEB;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
        font-size: 24px;
        color: #333;
    }

    /* 提示文字样式 */
    .hint-text {
        font-family: 'Courier New', monospace;
        font-size: 32px;
        font-weight: bold;
        color: #FF8C00;
        letter-spacing: 5px;
        text-align: center;
        margin: 10px 0;
    }

    /* 按钮样式升级：适合手指触摸的大按钮 */
    .stButton>button {
        width: 100%;
        border-radius: 25px; /* 圆圆的按钮 */
        height: 70px;        /* 增高，方便点击 */
        font-size: 24px !important;
        font-weight: bold;
        border: 3px solid #FFF;
        box-shadow: 0px 5px 0px #ccc; /* 3D按压效果 */
        transition: all 0.1s;
        color: #4A4A4A;
        background-color: #FFEFD5; /* 默认淡橙色 */
    }
    
    /* 按钮按下效果 */
    .stButton>button:active {
        box-shadow: 0px 2px 0px #ccc;
        transform: translateY(3px);
    }

    /* 针对不同按钮的颜色定制 (通过CSS选择器比较难精确控制，这里用统一风格) */
    
    /* 成功/失败的消息框字体加大 */
    .stAlert {
        font-size: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 辅助逻辑函数
# ==========================================

def generate_spelling_hint(word):
    """
    生成拼写提示
    策略：
    1. 30% 概率不给提示，只给下划线 (Hard)
    2. 70% 概率随机给出 1-2 个字母 (Easy)
    """
    length = len(word)
    
    # 如果词太短(<=3)，或者随机到了Hard模式，就不给字母
    if length <= 3 or random.random() < 0.3:
        return "_ " * length
    
    # 计算给几个字母：最少1个，最多是长度的一半减1（防止给太多）
    # 例如：apple(5) -> max 2个; banana(6) -> max 2个
    max_reveal = max(1, int(length / 2) - 1)
    num_to_reveal = random.randint(1, max_reveal)
    
    # 随机选几个位置显示字母
    indices_to_reveal = set(random.sample(range(length), num_to_reveal))
    
    hint_chars = []
    for i in range(length):
        if i in indices_to_reveal:
            hint_chars.append(word[i])
        else:
            hint_chars.append("_")
            
    return " ".join(hint_chars)

def init_learning_session(words):
    st.session_state.learning_queue = words
    st.session_state.progress_map = {w['id']: 0 for w in words}
    st.session_state.failed_attempts = set()
    st.session_state.matching_batch = []
    st.session_state.selected_word_id = None
    # 拼写相关状态
    if 'current_spelling_word' in st.session_state:
        del st.session_state['current_spelling_word']

def check_matching(word_id):
    if st.session_state.selected_word_id is None:
        st.session_state.selected_word_id = word_id
        return None
    
    if st.session_state.selected_word_id == word_id:
        st.session_state.progress_map[word_id] += 1
        st.success("Bingo! 配对成功！🎉") # Streamlit 气球会占用执行时间，暂且只显示文字
        time.sleep(0.5)
        st.session_state.selected_word_id = None
        st.rerun()
    else:
        st.error("Oops! 不对哦，再试试！")
        time.sleep(0.5)
        st.session_state.progress_map[st.session_state.selected_word_id] = 0
        st.session_state.progress_map[word_id] = 0
        st.session_state.selected_word_id = None

# ==========================================
# 3. 页面主逻辑
# ==========================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- 首页 ---
if st.session_state.page == 'home':
    st.title("🏰 单词魔法屋")
    st.write("")
    
    total, new_cnt = get_stats()
    
    # 两个大卡片显示数据
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"📚 单词总数: {total}")
    with c2:
        st.warning(f"🌱 待学新词: {new_cnt}")

    st.write("---")
    
    # 两个巨大的入口按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 学习新词\nStart New", use_container_width=True):
            words = get_random_new_words(20)
            if not words:
                st.warning("太棒了！所有单词都学完了！")
            else:
                init_learning_session(words)
                st.session_state.page = 'learning_matching'
                st.rerun()
                
    with col2:
        if st.button("🧠 复习旧词\nReview", use_container_width=True):
            st.info("复习功能即将上线...")

    # 家长控制台放在侧边栏最下方
    with st.sidebar:
        st.title("家长控制台")
        up = st.file_uploader("上传 Excel", type=['xlsx'])
        if up and st.button("导入数据"):
            ok, msg = import_from_excel(up)
            if ok: st.success(msg)
            else: st.error(msg)

# --- 学习：配对 ---
elif st.session_state.page == 'learning_matching':
    st.title("🧩 魔法连连看")
    
    need_matching = [w for w in st.session_state.learning_queue if st.session_state.progress_map[w['id']] < 1]
    
    if len(need_matching) == 0:
        st.session_state.page = 'learning_spelling'
        st.rerun()
    
    # 补货逻辑
    current_ids = [w['id'] for w in st.session_state.matching_batch]
    st.session_state.matching_batch = [w for w in st.session_state.matching_batch if st.session_state.progress_map[w['id']] < 1]
    
    while len(st.session_state.matching_batch) < 4 and len(need_matching) > len(st.session_state.matching_batch):
        candidates = [w for w in need_matching if w not in st.session_state.matching_batch]
        if not candidates: break
        st.session_state.matching_batch.append(random.choice(candidates))
        
    batch = st.session_state.matching_batch
    
    # 界面布局
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🔤 单词")
        for w in batch:
            label = w['word']
            # 选中状态加个标记
            if st.session_state.selected_word_id == w['id']:
                label = f"✨ {label} ✨"
            
            if st.button(label, key=f"w_{w['id']}", use_container_width=True):
                st.session_state.selected_word_id = w['id']
                
    with c2:
        st.markdown("### 📖 意思")
        shuffled = sorted(batch, key=lambda x: x['definition'])
        for w in shuffled:
            if st.button(w['definition'], key=f"d_{w['id']}", use_container_width=True):
                check_matching(w['id'])

    st.write("---")
    if st.button("⏩ 跳过配对 (测试用)"):
        st.session_state.page = 'learning_spelling'
        st.rerun()

# --- 学习：拼写 ---
elif st.session_state.page == 'learning_spelling':
    st.title("✍️ 单词拼写挑战")
    
    remaining = [w for w in st.session_state.learning_queue if st.session_state.progress_map[w['id']] < 2]
    
    if not remaining:
        st.balloons()
        st.markdown("""
        <div style="text-align:center; padding: 50px;">
            <h1>🌟 恭喜你！ 🌟</h1>
            <h3>今天的任务全部完成！</h3>
        </div>
        """, unsafe_allow_html=True)
        # 写入数据库
        for w in st.session_state.learning_queue:
            update_word_mastery(w['id'], True)
            
        if st.button("回到主页"):
            st.session_state.page = 'home'
            st.rerun()
        st.stop()

    # 初始化当前题目
    if 'current_spelling_word' not in st.session_state:
        st.session_state.current_spelling_word = random.choice(remaining)
        st.session_state.spelling_attempt = 0
        # 生成一个固定的提示，防止每次刷新页面提示都变
        st.session_state.current_hint = generate_spelling_hint(st.session_state.current_spelling_word['word'])
    
    target = st.session_state.current_spelling_word
    
    # 显示释义卡片
    st.markdown(f"""
    <div class="def-box">
        {target['definition']}
    </div>
    """, unsafe_allow_html=True)
    
    # 显示提示（随机字母或下划线）
    # 只有在还没答对的时候才显示提示
    st.markdown(f'<div class="hint-text">{st.session_state.current_hint}</div>', unsafe_allow_html=True)
    
    # 输入框
    user_input = st.text_input("在这里输入单词 (按回车确认):", key="spelling_inp").strip()
    
    col_submit, col_skip = st.columns([2, 1])
    
    with col_submit:
        if st.button("✨ 确定 ✨", use_container_width=True):
            if user_input.lower() == target['word'].lower():
                st.success("太棒了！拼写正确！🎈")
                time.sleep(1)
                
                # 第一次就对：直接过 (progress=2)
                # 否则：progress+1
                if st.session_state.spelling_attempt == 0:
                    st.session_state.progress_map[target['id']] = 2
                else:
                    st.session_state.progress_map[target['id']] += 1
                
                # 删掉当前词状态，触发下次重选
                del st.session_state['current_spelling_word']
                st.rerun()
            else:
                st.error(f"不对哦，正确是: {target['word']}")
                st.session_state.spelling_attempt += 1
                st.session_state.progress_map[target['id']] = 0 # 错了重头来
                # 错了之后，我们把提示改成全显示，或者不做操作让他照着抄
                st.info(f"请照着输入一遍: {target['word']}")
    
    with col_skip:
        if st.session_state.spelling_attempt > 0:
            if st.button("➡️ 下一个"):
                del st.session_state['current_spelling_word']
                st.rerun()

    st.markdown(f"**剩余挑战: {len(remaining)} 个**")