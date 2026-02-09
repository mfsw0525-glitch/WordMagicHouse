# db_manager.py
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "word_magic.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # 单词表
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            source_unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 进度表
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            word_id INTEGER PRIMARY KEY,
            status INTEGER DEFAULT 0,  -- 0:New, 1:Learning, 2:Review, 3:Mastered
            next_review_time DATE,
            interval INTEGER DEFAULT 0,
            proficiency INTEGER DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES vocabulary (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_random_new_words(limit=20):
    """
    【新功能】随机从所有 status=0 (未学) 的单词中抽取指定数量
    """
    conn = get_connection()
    # SQL 逻辑：查找在 progress 表中 status=0 的词，或者还不在 progress 表中的词
    # 这里为了简化，我们假设导入时已经初始化了 progress 表 (status=0)
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
    # 返回字典列表格式: [{'id':1, 'word':'apple', 'definition':'苹果'}, ...]
    return df.to_dict('records')

def import_from_excel(file_buffer):
    """
    【新功能】从 Excel 文件对象导入数据
    Excel 必须包含两列表头：'word' 和 'definition'
    """
    try:
        df = pd.read_excel(file_buffer)
        
        # 简单的列名检查与清洗
        df.columns = [c.lower().strip() for c in df.columns]
        if 'word' not in df.columns or 'definition' not in df.columns:
            return False, "Excel 必须包含 'word' 和 'definition' 列"
            
        conn = get_connection()
        c = conn.cursor()
        
        count = 0
        for _, row in df.iterrows():
            word = str(row['word']).strip()
            definition = str(row['definition']).strip()
            source = str(row.get('source', 'Upload')) # 可选列
            
            # 查重：如果单词已存在，跳过
            c.execute("SELECT id FROM vocabulary WHERE word = ?", (word,))
            if c.fetchone():
                continue
                
            c.execute("INSERT INTO vocabulary (word, definition, source_unit) VALUES (?, ?, ?)", 
                      (word, definition, source))
            new_id = c.lastrowid
            
            # 初始化进度
            c.execute("INSERT INTO learning_progress (word_id, status) VALUES (?, 0)", (new_id,))
            count += 1
            
        conn.commit()
        conn.close()
        return True, f"成功导入 {count} 个新单词！"
    except Exception as e:
        return False, f"导入失败: {str(e)}"

# 保留原有的批量添加功能，用于初始化脚本
def add_words_bulk(word_list):
    conn = get_connection()
    c = conn.cursor()
    data_to_insert = []
    for w, d, u in word_list:
        # 查重
        c.execute("SELECT id FROM vocabulary WHERE word = ?", (w,))
        if c.fetchone():
            continue
        data_to_insert.append((w, d, u))
        
    if data_to_insert:
        c.executemany('INSERT INTO vocabulary (word, definition, source_unit) VALUES (?, ?, ?)', data_to_insert)
        # 初始化进度
        c.execute('''
            INSERT INTO learning_progress (word_id, status, interval, proficiency)
            SELECT id, 0, 0, 0 FROM vocabulary 
            WHERE id NOT IN (SELECT word_id FROM learning_progress)
        ''')
        conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM vocabulary")
    total = c.fetchone()[0]
    c.execute("SELECT count(*) FROM learning_progress WHERE status=0")
    new_words = c.fetchone()[0]
    conn.close()
    return total, new_words

# 保持初始化
init_db()