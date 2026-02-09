# db_manager.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = "word_magic.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            source_unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            word_id INTEGER PRIMARY KEY,
            status INTEGER DEFAULT 0,  -- 0:New, 1:Learning/Reviewing
            next_review_time DATE,
            interval INTEGER DEFAULT 0,
            proficiency INTEGER DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES vocabulary (id)
        )
    ''')
    conn.commit()
    conn.close()

# --- 获取新词 (保持不变) ---
def get_random_new_words(limit=20):
    conn = get_connection()
    # 选取 status=0 的单词
    query = f'''
        SELECT v.id, v.word, v.definition 
        FROM vocabulary v
        JOIN learning_progress lp ON v.id = lp.word_id
        WHERE lp.status = 0
        ORDER BY RANDOM() 
        LIMIT {limit}
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict('records')

# --- 🆕 获取待复习单词 (New) ---
def get_words_for_review(limit=50):
    """
    获取 status > 0 且 next_review_time <= 今天 的单词
    """
    conn = get_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    
    query = f'''
        SELECT v.id, v.word, v.definition, lp.interval
        FROM vocabulary v
        JOIN learning_progress lp ON v.id = lp.word_id
        WHERE lp.status > 0 
          AND lp.next_review_time <= '{today}'
        ORDER BY lp.next_review_time ASC
        LIMIT {limit}
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict('records')

# --- 🆕 获取统计数据 (New: 增加复习计数) ---
def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM vocabulary")
    total = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM learning_progress WHERE status=0")
    new_words = c.fetchone()[0]
    
    # 统计今日待复习
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute(f"SELECT count(*) FROM learning_progress WHERE status > 0 AND next_review_time <= '{today}'")
    review_count = c.fetchone()[0]
    
    conn.close()
    return total, new_words, review_count

# --- 🆕 更新学习进度 (核心：艾宾浩斯逻辑) ---
def update_word_mastery(word_id, success=True):
    conn = get_connection()
    c = conn.cursor()
    
    # 1. 先查询该词当前的状态
    c.execute("SELECT status, interval FROM learning_progress WHERE word_id=?", (word_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return

    curr_status, curr_interval = row
    
    today = datetime.now()
    new_interval = 1
    new_status = 1
    
    if success:
        # ✅ 答对了
        if curr_status == 0:
            # 如果是新词第一次学完 -> 间隔设为 1 天
            new_interval = 1
        else:
            # 如果是复习 -> 间隔翻倍 (艾宾浩斯简化版: 1, 2, 4, 8...)
            # 如果当前间隔是0(异常情况)，修正为1
            base_interval = max(1, curr_interval)
            new_interval = base_interval * 2
    else:
        # ❌ 答错了 (忘记了)
        # 惩罚：重置间隔为 1 天，明天必须重测
        new_interval = 1
    
    # 计算下次复习日期
    next_date = (today + timedelta(days=new_interval)).strftime('%Y-%m-%d')
    
    c.execute('''
        UPDATE learning_progress 
        SET status = ?, 
            next_review_time = ?, 
            interval = ?,
            proficiency = proficiency + ?
        WHERE word_id = ?
    ''', (new_status, next_date, new_interval, 1 if success else 0, word_id))
    
    conn.commit()
    conn.close()

# --- 导入 Excel (保持不变) ---
def import_from_excel(file_buffer):
    try:
        df = pd.read_excel(file_buffer)
        df.columns = [c.lower().strip() for c in df.columns]
        if 'word' not in df.columns or 'definition' not in df.columns:
            return False, "Excel 必须包含 'word' 和 'definition' 列"
            
        conn = get_connection()
        c = conn.cursor()
        count = 0
        for _, row in df.iterrows():
            word = str(row['word']).strip()
            definition = str(row['definition']).strip()
            source = str(row.get('source', 'Upload'))
            c.execute("SELECT id FROM vocabulary WHERE word = ?", (word,))
            if c.fetchone(): continue
            c.execute("INSERT INTO vocabulary (word, definition, source_unit) VALUES (?, ?, ?)", (word, definition, source))
            new_id = c.lastrowid
            c.execute("INSERT INTO learning_progress (word_id, status) VALUES (?, 0)", (new_id,))
            count += 1
        conn.commit()
        conn.close()
        return True, f"成功导入 {count} 个新单词！"
    except Exception as e:
        return False, f"导入失败: {str(e)}"

init_db()