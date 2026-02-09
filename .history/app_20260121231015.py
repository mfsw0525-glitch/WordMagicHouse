# app.py
import streamlit as st
import random
import time
from db_manager import get_stats, import_from_excel, get_random_new_words, update_word_mastery

# ==========================================
# 配置与 CSS
# ==========================================
st.set_page_config(page_title="单词魔法屋", page_icon="🏰", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #F0F8FF; }
    h1 { color: #FF69B4; font-family: 'Comic Sans MS'; text-align: center; text-shadow: 2px 2px #FFD700; }
    .big-font { font-size: 24px !important; font-weight: bold; color: #333; }
    .def-box { background-color: #fff; padding: 20px; border-radius: 10px; border: 2px solid #87CEEB; margin-bottom: 20px; }
    .stButton>button { border-radius: 15px; font-size: 18px; font-weight: bold; border: 2px solid #eee; }
    /* 选中状态的按钮颜色 */
    .selected-btn { border: 3px solid #FF4500 !important; background-color: #FFE4B5 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 辅助函数：学习逻辑
# ==========================================

def init_learning_session(words):
    """初始化学习 session"""
    st.session_state.learning_queue = words  # 当前待学的20个词
    st.session_state.progress_map = {w['id']: 0 for w in words} # 记录每个词的连对次数
    st.session_state.failed_attempts = set() # 记录哪些词拼写错过（错过的要隔3次再现）
    
    # 游戏模式状态
    st.session_state.current_mode = 'matching' # matching, spelling
    st.session_state.matching_batch = []     # 配对游戏的当前4个词
    st.session_state.selected_word_id = None # 配对游戏中当前选中的词ID

def get_remaining_words():
    """获取尚未完成学习的单词"""
    # 完成标准：连对次数 >= 2
    return [w for w in st.session_state.learning_queue if st.session_state.progress_map[w['id']] < 2]

def check_matching(word_id):
    """配对游戏：检查是否匹配"""
    if st.session_state.selected_word_id is None:
        st.session_state.selected_word_id = word_id
        return None
    
    if st.session_state.selected_word_id == word_id:
        # 配对成功！
        st.session_state.progress_map[word_id] += 1 # 进度+1
        st.balloons()
        st.success("Bingo! 配对成功！🎉")
        time.sleep(1)
        st.session_state.selected_word_id = None
        # 从当前批次移除，刷新页面会重新抽取
        st.rerun()
    else:
        # 配对失败
        st.error("Oops! 不对哦，再试试！")
        st.session_state.progress_map[st.session_state.selected_word_id] = 0 # 失败清零
        st.session_state.progress_map[word_id] = 0
        st.session_state.selected_word_id = None

# ==========================================
# 页面逻辑
# ==========================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- 1. 主页 Home ---
if st.session_state.page == 'home':
    st.title("🏰 Word Magic House")
    
    # 统计卡片
    total, new_cnt = get_stats()
    c1, c2 = st.columns(2)
    c1.metric("📚 魔法书总单词", total)
    c2.metric("🌱 等你来探索", new_cnt)
    
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 开始学习 (Start New)", use_container_width=True):
            words = get_random_new_words(20)
            if not words:
                st.warning("所有单词都学完啦！请家长导入新词。")
            else:
                init_learning_session(words)
                st.session_state.page = 'learning_matching'
                st.rerun()
                
    with col2:
        if st.button("🧠 复习旧词 (Review)", use_container_width=True):
            st.info("复习功能将在下一步上线！")

    # 侧边栏：家长上传
    with st.sidebar:
        st.header("家长控制台")
        up_file = st.file_uploader("上传 Excel", type=['xlsx'])
        if up_file and st.button("导入"):
            ok, msg = import_from_excel(up_file)
            if ok: st.success(msg)
            else: st.error(msg)

# --- 2. 学习阶段：配对游戏 (Matching) ---
elif st.session_state.page == 'learning_matching':
    st.title("🧩 魔法连连看")
    st.caption("请把单词和意思连起来！(连续做对两次通过)")
    
    # 1. 筛选出还需要做“配对练习”的词
    # 规则：如果进度 < 1 (还未熟悉)，优先做配对。如果大家都熟悉了(>=1)，进入拼写阶段
    need_matching = [w for w in st.session_state.learning_queue if st.session_state.progress_map[w['id']] < 1]
    
    # 如果所有词都至少对过一次配对，或者剩余词很少，进入拼写阶段
    if len(need_matching) == 0:
        st.session_state.page = 'learning_spelling'
        st.rerun()
    
    # 2. 准备一局游戏的 4 个词
    # 如果当前没有 batch，或者 batch 里的词被消完了，就重新补货
    current_ids = [w['id'] for w in st.session_state.matching_batch]
    # 过滤掉已经不需要配对的词
    st.session_state.matching_batch = [w for w in st.session_state.matching_batch if st.session_state.progress_map[w['id']] < 1]
    
    # 补货到4个
    while len(st.session_state.matching_batch) < 4 and len(need_matching) > len(st.session_state.matching_batch):
        # 从 need_matching 里选一个不在 current_batch 里的
        candidates = [w for w in need_matching if w not in st.session_state.matching_batch]
        if not candidates: break
        st.session_state.matching_batch.append(random.choice(candidates))
        
    batch = st.session_state.matching_batch
    
    # 3. 渲染界面
    # 左边放单词，右边放释义（打乱）
    # 为了避免每次刷新都乱序，我们需要一个固定的 shuffle 种子，或者简单点，每次根据ID排序显示
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("单词 (Words)")
        for word_obj in batch:
            # 按钮样式：如果被选中，显示高亮（这里用emoji模拟，Streamlit原生按钮很难改色）
            label = word_obj['word']
            if st.session_state.selected_word_id == word_obj['id']:
                label = f"✅ {label}"
            
            if st.button(label, key=f"btn_word_{word_obj['id']}", use_container_width=True):
                st.session_state.selected_word_id = word_obj['id']
                # 不 rerurn，等待点右边
                
    with col_b:
        st.subheader("意思 (Meaning)")
        # 释义需要打乱顺序显示，不然就是一行对了
        # 我们用一个简单的临时列表来存，为了保证顺序固定，可以用 batch 的倒序或者其他逻辑
        shuffled_defs = sorted(batch, key=lambda x: x['definition']) 
        
        for word_obj in shuffled_defs:
            if st.button(word_obj['definition'], key=f"btn_def_{word_obj['id']}", use_container_width=True):
                check_matching(word_obj['id'])
    
    st.write("---")
    st.write(f"当前队列剩余新词: {len(need_matching)} 个")
    if st.button("跳过配对，直接去拼写"):
        st.session_state.page = 'learning_spelling'
        st.rerun()

# --- 3. 学习阶段：拼写特训 (Spelling) ---
elif st.session_state.page == 'learning_spelling':
    st.title("✍️ 单词拼写挑战")
    
    # 1. 获取还需要拼写的词 (progress < 2)
    remaining = get_remaining_words()
    
    if not remaining:
        st.balloons()
        st.success("太棒了！今天的 20 个单词全部掌握！")
        # 将结果写入数据库
        for w in st.session_state.learning_queue:
            update_word_mastery(w['id'], success=True)
        
        if st.button("回到主页"):
            st.session_state.page = 'home'
            st.rerun()
        st.stop()

    # 2. 选一个词来考 (随机)
    if 'current_spelling_word' not in st.session_state:
        st.session_state.current_spelling_word = random.choice(remaining)
        st.session_state.spelling_attempt_count = 0 # 记录当前词错了没
    
    target_word = st.session_state.current_spelling_word
    
    # 3. 显示题目
    st.markdown(f"""
        <div class="def-box">
            <h3>{target_word['definition']}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # 提示逻辑
    # 第一次：显示 _ _ _ (位数)
    # 错一次后：显示 word 但挖空
    hint_text = ""
    if st.session_state.spelling_attempt_count == 0:
        hint_text = "提示: " + " ".join(["_"] * len(target_word['word']))
    else:
        # 显示首字母
        w = target_word['word']
        hint_text = f"提示: {w[0]}..." + " (再试一次)"
    
    st.info(hint_text)
    
    # 4. 输入框
    user_input = st.text_input("请输入单词:", key="spelling_input").strip()
    
    # 5. 提交按钮逻辑
    if st.button("确定"):
        if user_input.lower() == target_word['word'].lower():
            st.success("拼对啦！🎉")
            st.balloons()
            time.sleep(1)
            
            # 逻辑：第一次就拼对，算掌握 (progress设为2)
            # 之前错过拼对，progress + 1
            if st.session_state.spelling_attempt_count == 0:
                st.session_state.progress_map[target_word['id']] = 2 # 直接通过
            else:
                st.session_state.progress_map[target_word['id']] += 1
            
            # 清除当前词，准备下一个
            del st.session_state['current_spelling_word']
            st.rerun()
        else:
            st.error(f"不对哦，正确答案是: {target_word['word']}")
            st.session_state.spelling_attempt_count += 1
            # 错误惩罚：进度清零或扣分（这里简化为不增加进度）
            st.session_state.progress_map[target_word['id']] = 0 
            
            # 强制要求用户输入正确答案才能过（这里简化为点确定后，如果不重置session_state key，就会继续留在这里）
            # 我们给一个"我看清楚了"的按钮
    
    # 如果拼错了，显示“下一个”按钮来刷新
    if st.session_state.spelling_attempt_count > 0:
        if st.button("记住了，下一个"):
            # 换一个词，把这个词放回队列后面
            del st.session_state['current_spelling_word']
            st.rerun()

    st.write(f"剩余挑战: {len(remaining)} 个")