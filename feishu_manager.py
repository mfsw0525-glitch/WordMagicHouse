import requests
import json
import logging
import random
from datetime import datetime, timedelta

# --- Configuration ---
# 请填写你的实际值
APP_ID = "cli_a903e0aa56b8dbc8"
APP_SECRET = "FfzPc5W4Aom4a5MKvKPnfg0BDNRND0c5"
BASE_TOKEN = "Af53bVxVEaTWIRsnDy6cBo83nSf" # 确认有效的 Base Token
TABLE_ID = "tbluB7I2xtUtkIX5"

class FeishuManager:
    def __init__(self):
        self.tenant_access_token = ""
        self.token_expire_time = 0
        
    def _get_tenant_access_token(self):
        # 简单缓存 Token
        if self.tenant_access_token and datetime.now().timestamp() < self.token_expire_time:
            return self.tenant_access_token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload)
            data = resp.json()
            if data.get("code") == 0:
                self.tenant_access_token = data.get("tenant_access_token")
                # 提前 5 分钟过期
                self.token_expire_time = datetime.now().timestamp() + data.get("expire") - 300
                return self.tenant_access_token
            else:
                logging.error(f"Failed to get tenant_access_token: {data}")
                return None
        except Exception as e:
            logging.error(f"Error getting token: {e}")
            return None

    def _request(self, method, endpoint, params=None, json_data=None):
        token = self._get_tenant_access_token()
        if not token: return None
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            resp = requests.request(method, url, headers=headers, params=params, json=json_data)
            return resp.json()
        except Exception as e:
            logging.error(f"Request error: {e}")
            return None

    # --- 核心业务逻辑 ---

    def get_stats(self):
        """获取统计数据: 总词数, 新词数, 待复习数, 已学数"""
        # 1. 总词数
        res = self._request("GET", f"tables/{TABLE_ID}/records", params={"page_size": 1}) # 只取一条看 total
        total = res['data']['total'] if res and res.get('code') == 0 else 0
        
        # 2. 新词数 (status = 0)
        # filter: CurrentValue.[status]=0
        conditions = 'CurrentValue.[status]=0'
        res_new = self._request("GET", f"tables/{TABLE_ID}/records", params={"filter": conditions, "page_size": 1})
        new_cnt = res_new['data']['total'] if res_new and res_new.get('code') == 0 else 0
        
        # 3. 待复习数 (status > 0 AND next_review_time <= Now)
        # 注意飞书的时间格式通常是毫秒级时间戳，或者 YYYY/MM/DD 格式
        # 简单的做法是把所有 status > 0 的拉下来在内存里算（如果数据量不大）
        # 或者使用 filter 语法。飞书 filter 对日期比较支持得一般，我们先拉取 status > 0 的所有记录
        conditions_learned = 'CurrentValue.[status]>0'
        res_learned = self._request("GET", f"tables/{TABLE_ID}/records", params={"filter": conditions_learned, "page_size": 500}) # 假设已学不超过 500
        
        review_cnt = 0
        learned_cnt = 0
        
        if res_learned and res_learned.get('code') == 0:
            learned_cnt = res_learned['data'].get('total', 0)
            items = res_learned['data'].get('items', [])
            now_ts = int(datetime.now().timestamp() * 1000) # 毫秒
            
            for item in items:
                fields = item['fields']
                next_time = fields.get('next_review_time', 0)
                # 飞书 API 返回的日期通常是毫秒时间戳
                if isinstance(next_time, int) and next_time <= now_ts:
                    review_cnt += 1
                    
        return total, new_cnt, review_cnt, learned_cnt

    def get_random_new_words(self, limit=20):
        """获取随机新词"""
        # 1. 获取所有 status=0 的记录
        conditions = 'CurrentValue.[status]=0'
        res = self._request("GET", f"tables/{TABLE_ID}/records", params={"filter": conditions, "page_size": 100})
        
        words = []
        if res and res.get('code') == 0:
            items = res['data']['items']
            # 随机取
            selected_items = random.sample(items, min(len(items), limit))
            for item in selected_items:
                fields = item['fields']
                words.append({
                    'id': item['record_id'], # 使用 record_id 作为唯一标识
                    'word': fields.get('word', ''),
                    'definition': fields.get('definition', '')
                })
        return words

    def update_word_mastery(self, record_id, success=True):
        """更新单词掌握情况"""
        # 1. 先读取当前记录
        res = self._request("GET", f"tables/{TABLE_ID}/records/{record_id}")
        if not res or res.get('code') != 0: return
        
        fields = res['data']['record']['fields']
        curr_status = fields.get('status', 0)
        curr_interval = fields.get('interval', 0)
        curr_proficiency = fields.get('proficiency', 0)
        
        today = datetime.now()
        new_interval = 1
        new_status = 1
        
        if success:
            if curr_status == 0:
                new_interval = 1
            else:
                base_interval = max(1, curr_interval)
                new_interval = base_interval * 2
        else:
            new_interval = 1
            
        next_date = today + timedelta(days=new_interval)
        next_ts = int(next_date.timestamp() * 1000) # 转为毫秒时间戳
        
        update_fields = {
            "status": new_status,
            "next_review_time": next_ts,
            "interval": new_interval,
            "proficiency": curr_proficiency + (1 if success else 0)
        }
        
        # 2. 更新记录
        self._request("PUT", f"tables/{TABLE_ID}/records/{record_id}", json_data={"fields": update_fields})

    def import_from_excel(self, file_buffer):
        pass # 暂未实现，飞书导入比较复杂，建议直接在飞书界面导入

    def test_connection(self):
        # Try to list records to verify everything
        res = self._request("GET", f"tables/{TABLE_ID}/records", params={"page_size": 1})
        if res and res.get("code") == 0:
            print("✅ Connection Successful!")
            total = res['data']['total']
            print(f"Found {total} records in table.")
            if total > 0:
                print("First record sample:", res['data']['items'][0]['fields'])
            return True
        else:
            print("❌ Connection Failed")
            print(res)
            return False

# Global Instance
fm = FeishuManager()

# Wrapper functions for app.py compatibility
def get_stats():
    return fm.get_stats()

def get_random_new_words(limit=20):
    return fm.get_random_new_words(limit)

def update_word_mastery(word_id, success=True):
    return fm.update_word_mastery(word_id, success)

def import_from_excel(file_buffer): 
    return False, "请直接在飞书多维表格界面导入 Excel 数据"

if __name__ == "__main__":
    fm.test_connection()
    print("Testing get_stats:", fm.get_stats())
