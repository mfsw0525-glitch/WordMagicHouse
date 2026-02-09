# import_data.py
from db_manager import init_db, add_words_bulk, get_stats

# 这里我把您 Unit 1 到 Unit 10 的数据整理成了一个列表
# 为了演示方便，我放入了部分数据。
# 您可以直接运行这个脚本，它会把这些词存入数据库。

raw_data = [
    # Unit 1
    ("beach", "an area of sand or rocks next to the sea", "Unit 1"),
    ("cousin", "a child of your uncle or aunt", "Unit 1"),
    ("friend", "someone who you know well and like", "Unit 1"),
    ("holiday", "a time when you do not have to go to work or school", "Unit 1"),
    ("idea", "a plan of action", "Unit 1"),
    ("lemonade", "a drink made usually of lemon juice, sugar, and water", "Unit 1"),
    ("scientist", "someone who studies science or works in science", "Unit 1"),
    ("fair", "of a person's hair, skin, etc., having a light color", "Unit 1"),
    ("shark", "a large and often dangerous sea fish with very sharp teeth", "Unit 1"),
    ("clever", "able to learn and understand things quickly and easily", "Unit 1"),
    ("trick", "something done to surprise or cheat someone", "Unit 1"),
    ("old", "having lived for a long time", "Unit 1"),
    ("beautiful", "very attractive", "Unit 1"),
    ("grey", "having a colour between black and white", "Unit 1"),
    ("funny", "making you smile or laugh", "Unit 1"),
    ("dark", "black or brown in colour", "Unit 1"),
    ("stupid", "silly or not smart", "Unit 1"),
    ("cold", "having a low temperature", "Unit 1"),
    ("house", "a building where people live", "Unit 1"),
    ("hungry", "wanting or needing food", "Unit 1"),
    ("ugly", "unpleasant to look at", "Unit 1"),
    
    # Unit 2 (演示跨单元分组)
    ("computer game", "a game that is played on a computer", "Unit 2"),
    ("laptop", "a small computer to be carried around", "Unit 2"),
    ("lots of", "a large number or amount of", "Unit 2"),
    ("board game", "a game that is played on a board", "Unit 2"),
    ("toy", "something a child plays with", "Unit 2"),
    ("touch", "to put your hand on something", "Unit 2"),
    ("message", "information that one person gives to another", "Unit 2"),
    ("museum", "a building for art, history, or science", "Unit 2"),
    ("strange", "surprising because not usual", "Unit 2"),
    ("puzzle", "a game using skill", "Unit 2"),
]

# 这里只是演示数据，如果您想导入全部，
# 后面我们可以做一个文本文件读取功能，或者您把刚才的文本都贴进来。

def run_import():
    # 1. 确保数据库存在
    init_db()
    
    # 2. 导入数据
    print("正在导入数据...")
    add_words_bulk(raw_data)
    
    # 3. 验证结果
    total, new_words = get_stats()
    print("-" * 30)
    print(f"📊 数据库统计:")
    print(f"总单词数: {total}")
    print(f"待学新词: {new_words}")
    print("-" * 30)

if __name__ == "__main__":
    run_import()