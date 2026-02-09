# check_db.py
import sqlite3
import pandas as pd
from db_manager import get_random_new_words

DB_NAME = "word_magic.db"

def inspect_db():
    print(f"🔍 正在检查数据库: {DB_NAME}...\n")
    conn = sqlite3.connect(DB_NAME)
    
    # 1. 检查表结构
    print("="*30)
    print("📋 表结构 (Schema)")
    print("="*30)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        t_name = table_name[0]
        if t_name == "sqlite_sequence": continue # 跳过系统表
        
        print(f"\n[表名: {t_name}]")
        # 获取列信息
        columns = pd.read_sql_query(f"PRAGMA table_info({t_name})", conn)
        # 简化显示，只看列名和类型
        print(columns[['name', 'type', 'pk']])
        
        # 获取行数
        count = pd.read_sql_query(f"SELECT count(*) FROM {t_name}", conn).iloc[0,0]
        print(f"--> 总行数: {count}")

    # 2. 检查数据内容 (随机抽样)
    print("\n" + "="*30)
    print("👀 数据内容抽样 (Vocabulary)")
    print("="*30)
    
    # 读取前5条看看样子
    df_sample = pd.read_sql_query("SELECT * FROM vocabulary LIMIT 5", conn)
    print(df_sample)
    
    # 3. 检查进度表关联
    print("\n" + "="*30)
    print("🔗 进度表关联检查 (Learning Progress)")
    print("="*30)
    progress_count = pd.read_sql_query("SELECT count(*) FROM learning_progress", conn).iloc[0,0]
    print(f"进度表记录数: {progress_count}")
    
    if progress_count > 0:
        # 看看状态分布
        status_dist = pd.read_sql_query("SELECT status, count(*) as num FROM learning_progress GROUP BY status", conn)
        print("\n状态分布 (0:新词, 1:学习中, 2:复习, 3:已掌握):")
        print(status_dist)
    else:
        print("⚠️ 警告: 进度表为空！这可能导致无法开始学习。")

    conn.close()

    # 4. 测试随机抽取功能
    print("\n" + "="*30)
    print("🎲 测试随机抽取逻辑 (db_manager)")
    print("="*30)
    try:
        random_words = get_random_new_words(limit=5)
        print(f"成功随机抽取了 {len(random_words)} 个单词:")
        for w in random_words:
            print(f"- {w['word']}: {w['definition']}")
    except Exception as e:
        print(f"❌ 随机抽取失败: {e}")

if __name__ == "__main__":
    inspect_db()