import sqlite3
import pandas as pd
from feishu_manager import fm, TABLE_ID

# 1. 从 SQLite 读取现有单词
conn = sqlite3.connect("word_magic.db")
query = '''
    SELECT word, definition 
    FROM vocabulary 
'''
df = pd.read_sql_query(query, conn)
conn.close()

print(f"📦 发现 {len(df)} 个本地单词。")

# 2. 导出为 Excel (备用)
df.to_excel("local_words_backup.xlsx", index=False)
print("💾 已备份到 local_words_backup.xlsx")

# 3. 批量写入飞书
print("🚀 开始上传到飞书 (每次 100 条)...")

# Feishu API supports batch creating records (max 100 per request)
records = []
for index, row in df.iterrows():
    # 构造符合飞书要求的字段
    # 注意: 全部设为未学习 (status=0)
    record = {
        "fields": {
            "word": str(row['word']),
            "definition": str(row['definition']),
            "status": 0,
            "next_review_time": 0, # 或者当前时间戳
            "interval": 0,
            "proficiency": 0
        }
    }
    records.append(record)
    
    # 每 100 条发送一次
    if len(records) >= 100:
        res = fm._request("POST", f"tables/{TABLE_ID}/records/batch_create", json_data={"records": records})
        if res and res.get('code') == 0:
            print(f"✅ 成功上传 100 条")
        else:
            print(f"❌ 上传失败: {res}")
        records = []

# 处理剩余的
if records:
    res = fm._request("POST", f"tables/{TABLE_ID}/records/batch_create", json_data={"records": records})
    if res and res.get('code') == 0:
        print(f"✅ 成功上传 {len(records)} 条")
    else:
        print(f"❌ 上传失败: {res}")

print("✨ 全部迁移完成！")
