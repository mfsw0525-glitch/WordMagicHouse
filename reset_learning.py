# reset_learning.py
import time
from data_manager import dm

def reset_all_words():
    print("🔄 正在从飞书获取所有已学单词...")
    # 获取所有 status > 0 的记录（即有过学习记录的词）
    all_learned = dm._fetch_all_learned()
    
    if not all_learned:
        print("✅ 没有发现已学习的单词，无需重置。")
        return

    print(f"📦 发现 {len(all_learned)} 个已学单词，准备重置...")
    
    # 构造重置字段
    reset_fields = {
        "status": 0,
        "next_review_time": 0,
        "interval": 0,
        "proficiency": 0
    }

    # 飞书 API 支持批量更新 (每次最多 100 条)
    records_to_update = []
    for item in all_learned:
        records_to_update.append({
            "record_id": item['record_id'],
            "fields": reset_fields
        })

        if len(records_to_update) >= 100:
            print(f"🚀 正在重置 100 个单词...")
            dm._request("POST", f"tables/{dm.table_id}/records/batch_update", json_data={"records": records_to_update})
            records_to_update = []
            time.sleep(0.5) # 稍微停顿，避免触发频率限制

    if records_to_update:
        print(f"🚀 正在重置剩余 {len(records_to_update)} 个单词...")
        dm._request("POST", f"tables/{dm.table_id}/records/batch_update", json_data={"records": records_to_update})

    print("✨ 全部单词已重置为“未学习”状态！女儿现在可以从头开始了。")

if __name__ == "__main__":
    import sys
    
    # 支持 -y 或 --yes 参数，跳过确认
    if '-y' in sys.argv or '--yes' in sys.argv:
        reset_all_words()
    else:
        try:
            confirm = input("⚠️  确定要重置所有学习进度吗？这将不可逆！(y/n): ")
            if confirm.lower() == 'y':
                reset_all_words()
            else:
                print("操作已取消。")
        except EOFError:
            print("\n❌ 错误：无法读取输入。")
            print("💡 提示：在非交互式环境中，请使用 '-y' 参数：")
            print("   python reset_learning.py -y")
            sys.exit(1)
