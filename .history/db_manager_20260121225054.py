# db_manager.py
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "word_magic.db"

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    """初始化数据库，创建两张核心表"""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. 单词表 (vocabulary)
    # group_id: 用于标记这批单词属于第几组（方便按组学习）
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            source_unit TEXT,
            group_id INTEGER, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. 学习进度表 (learning_progress)
    # status: 0=未学(New), 1=学习中(Learning), 2=需复习(Review), 3=已掌握(Mastered)
    # next_review_time: 下次复习的日期
    # interval: 当前复习间隔(天)，遵循艾宾浩斯 1, 2, 4, 7...
    # proficiency: 熟练度，用于记录连续答对次数
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            word_id INTEGER PRIMARY KEY,
            status INTEGER DEFAULT 0,
            next_review_time DATE,
            interval INTEGER DEFAULT 0,
            proficiency INTEGER DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES vocabulary (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成！表结构已建立。")

def add_words_bulk(word_list):
    """
    批量插入单词
    word_list 格式: [(word, definition, source_unit), ...]
    """
    conn = get_connection()
    c = conn.cursor()
    
    # 1. 先计算当前已有的最大 group_id，新进来的词顺延分组
    c.execute("SELECT MAX(group_id) FROM vocabulary")
    result = c.fetchone()[0]
    current_max_group = result if result is not None else 0
    
    # 2. 准备插入数据
    # 我们按照每20个单词一组，自动分配 group_id
    data_to_insert = []
    for index, (word, definition, unit) in enumerate(word_list):
        # 计算该单词应该属于第几组 (每20个一组)
        # 例如：如果是第1个词，组号是 current + 1
        # 如果是第21个词，组号是 current + 2
        group_increment = (index // 20) + 1
        new_group_id = current_max_group + group_increment
        
        data_to_insert.append((word, definition, unit, new_group_id))
        
    c.executemany('''
        INSERT INTO vocabulary (word, definition, source_unit, group_id)
        VALUES (?, ?, ?, ?)
    ''', data_to_insert)
    
    # 3. 同步初始化这些词的进度表（状态默认为0-未学）
    # 获取刚刚插入的单词的 rowid
    # 注意：SQLite的executemany很难直接拿回所有ID，这里我们用个简单策略：
    # 插入完单词后，为所有不在 progress 表里的单词插入一条初始记录
    c.execute('''
        INSERT INTO learning_progress (word_id, status, interval, proficiency)
        SELECT id, 0, 0, 0 FROM vocabulary 
        WHERE id NOT IN (SELECT word_id FROM learning_progress)
    ''')

    conn.commit()
    print(f"🎉 成功导入 {len(data_to_insert)} 个单词！")
    conn.close()

def get_stats():
    """查看一下当前数据库有多少词"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM vocabulary")
    total = c.fetchone()[0]
    c.execute("SELECT count(*) FROM learning_progress WHERE status=0")
    new_words = c.fetchone()[0]
    conn.close()
    return total, new_words

if __name__ == "__main__":
    # 如果直接运行这个文件，就执行初始化
    init_db()