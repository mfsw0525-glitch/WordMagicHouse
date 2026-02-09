# data_manager.py
import requests
import logging
import random
import threading
from datetime import datetime, timedelta
from config import *

class DataManager:
    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self.base_token = FEISHU_BASE_TOKEN
        self.table_id = FEISHU_TABLE_ID
        self.user_stats_table_id = FEISHU_USER_STATS_TABLE_ID
        self.tenant_access_token = ""
        self.token_expire_time = 0
        
    def _get_tenant_access_token(self):
        if self.tenant_access_token and datetime.now().timestamp() < self.token_expire_time:
            return self.tenant_access_token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        
        try:
            resp = requests.post(url, headers=headers, json=payload)
            data = resp.json()
            if data.get("code") == 0:
                self.tenant_access_token = data.get("tenant_access_token")
                self.token_expire_time = datetime.now().timestamp() + data.get("expire") - 300
                return self.tenant_access_token
            else:
                logging.error(f"Failed to get token: {data}")
                return None
        except Exception as e:
            logging.error(f"Error getting token: {e}")
            return None

    def _request(self, method, endpoint, params=None, json_data=None):
        token = self._get_tenant_access_token()
        if not token: return None
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}/{endpoint}"
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

    # --- User Stats (Streaks) ---
    def get_user_stats(self, user_id="daughter"):
        """Fetch streak from UserStats table"""
        res = self._request("GET", f"tables/{self.user_stats_table_id}/records", params={
            "filter": f'CurrentValue.[user_id]="{user_id}"'
        })
        if res and res.get('code') == 0 and res['data'].get('items'):
            item = res['data']['items'][0]
            fields = item['fields']
            return {
                "record_id": item['record_id'],
                "streak_days": int(fields.get("streak_days", 0)),
                "last_login": fields.get("last_login", "")
            }
        # If not found, create one
        return self._create_user_stats(user_id)

    def _create_user_stats(self, user_id):
        fields = {
            "user_id": user_id,
            "streak_days": 1,
            "last_login": int(datetime.now().timestamp() * 1000)
        }
        res = self._request("POST", f"tables/{self.user_stats_table_id}/records", json_data={"fields": fields})
        if res and res.get('code') == 0:
            return {
                "record_id": res['data']['record']['record_id'],
                "streak_days": 1, "last_login": ""
            }
        return {"record_id": "", "streak_days": 0, "last_login": ""}

    # --- Learning Data ---
    def get_stats(self):
        """
        Returns (total_words, new_words, review_words, mastered_words)
        ULTRA-OPTIMIZED: Efficiently handles multi-page vocab.
        """
        total = 0
        new_cnt = 0
        learned_cnt = 0
        review_cnt = 0
        
        now_ts = int(datetime.now().timestamp() * 1000)
        page_token = ""
        
        # We might need multiple pages if vocab > 500
        while True:
            params = {
                "field_names": '["status","next_review_time"]',
                "page_size": 500
            }
            if page_token: params["page_token"] = page_token
            
            res = self._request("GET", f"tables/{self.table_id}/records", params=params)
            if not res or res.get('code') != 0: break
            
            data = res['data']
            total = data['total'] # Accurate total from metadata
            items = data.get('items', [])
            
            for item in items:
                # Robust status check (handle string '0' or int 0)
                status_raw = item['fields'].get('status', 0)
                try:
                    status = int(status_raw)
                except (ValueError, TypeError):
                    status = 0
                
                if status == 0:
                    new_cnt += 1
                else:
                    learned_cnt += 1
                    next_time = item['fields'].get('next_review_time', 0)
                    if next_time <= now_ts:
                        review_cnt += 1
            
            if not data.get('has_more'): break
            page_token = data.get('page_token')
            
        # If we failed to get total, use counter
        if total == 0: total = new_cnt + learned_cnt
        
        return total, new_cnt, review_cnt, learned_cnt
        return total, new_cnt, review_cnt, learned_cnt

    def _fetch_all_learned(self):
        """Helper to fetch all records with status != 0 using pagination"""
        all_items = []
        page_token = ""
        while True:
            # Note: Using filter status >= 0 to get everything and then filter in Python
            # because string '0' vs int 0 issues in Bitable filter syntax
            params = {"page_size": 500}
            if page_token: params["page_token"] = page_token
            
            res = self._request("GET", f"tables/{self.table_id}/records", params=params)
            if res and res.get('code') == 0:
                data = res['data']
                items = data.get('items', [])
                for item in items:
                    raw_status = item['fields'].get('status', 0)
                    try:
                        status = int(raw_status)
                    except (ValueError, TypeError):
                        status = 0
                    
                    if status != 0:
                        all_items.append(item)
                
                if not data.get('has_more'): break
                page_token = data.get('page_token')
            else:
                break
        return all_items

    def get_new_words(self, limit=20):
        """Fetch new words (optimized for speed)"""
        res = self._request("GET", f"tables/{self.table_id}/records", params={
            "filter": 'CurrentValue.[status]=0',
            "field_names": '["word","definition"]',  # Only fetch what we need
            "page_size": min(limit * 3, 60)  # Fetch 3x for randomization pool
        })
        words = []
        if res and res.get('code') == 0:
            items = res['data'].get('items', [])
            selected = random.sample(items, min(len(items), limit))
            for item in selected:
                words.append({
                    'id': item['record_id'],
                    'word': item['fields'].get('word', ''),
                    'definition': item['fields'].get('definition', ''),
                    'status': 0, 'interval': 0
                })
        return words

    def get_review_words(self, limit=None):
        """Get words due for review (optimized with server-side filtering)"""
        now_ts = int(datetime.now().timestamp() * 1000)
        
        # Use server-side date filtering (much faster than fetching all and filtering client-side)
        res = self._request("GET", f"tables/{self.table_id}/records", params={
            "filter": f'CurrentValue.[status]>0 && CurrentValue.[next_review_time]<={now_ts}',
            "field_names": '["word","definition","status","interval","next_review_time"]',
            "page_size": 200  # Should cover most review sessions
        })
        
        if not res or res.get('code') != 0:
            return []
        
        items = res['data'].get('items', [])
        # Sort by due time (earliest first)
        items.sort(key=lambda x: x['fields'].get('next_review_time', 0))
        
        if limit:
            items = items[:limit]
        
        words = []
        for item in items:
            words.append({
                'id': item['record_id'],
                'word': item['fields'].get('word', ''),
                'definition': item['fields'].get('definition', ''),
                'status': item['fields'].get('status', 1),
                'interval': item['fields'].get('interval', 0),
            })
        return words

    def update_word_progress(self, record_id, is_correct, current_interval):
        """
        Update word progress. Optimizing to reduce UI lag.
        """
        if is_correct:
            if current_interval == 0: 
                new_interval = 1
            elif current_interval in REVIEW_INTERVALS:
                idx = REVIEW_INTERVALS.index(current_interval)
                new_interval = REVIEW_INTERVALS[idx + 1] if idx < len(REVIEW_INTERVALS) - 1 else REVIEW_INTERVALS[-1]
            else:
                new_interval = max(1, current_interval * 2)
        else:
            new_interval = 1
            
        next_date = datetime.now() + timedelta(days=new_interval)
        next_ts = int(next_date.timestamp() * 1000)
        
        fields = {
            "status": 1,
            "next_review_time": next_ts,
            "interval": new_interval
        }
        
        self._request("PUT", f"tables/{self.table_id}/records/{record_id}", json_data={"fields": fields})
        return new_interval

    def update_word_progress_async(self, record_id, is_correct, current_interval):
        """Spawns a background thread to update Feishu without blocking the UI"""
        import threading
        thread = threading.Thread(
            target=self.update_word_progress,
            args=(record_id, is_correct, current_interval)
        )
        thread.daemon = True # Ensure it doesn't block app exit
        thread.start()
        return True

    def send_bot_notification(self, session_type, count, streak=0):
        """Send a formatted message to Feishu Webhook"""
        if not FEISHU_WEBHOOK: return
        
        title = "🎉 学习战报 (Learning Report)"
        color = "blue"
        message = ""
        
        if session_type == "new":
            title = "🆕 新词挑战完成！"
            color = "green"
            message = f"🌟 小主人刚刚完成了 **{count}** 个新单词的学习！\n"
        else:
            title = "🔄 复习任务达成！"
            color = "orange"
            message = f"✅ 今日的复习任务已全部完成，共复习了 **{count}** 个单词！\n"
            
        message += f"🔥 当前连续打卡：**{streak}** 天\n"
        message += f"📅 记录时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"

        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": message}
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [{"tag": "plain_text", "content": "城堡的小精灵在为你欢呼！🏰✨"}]
                    }
                ]
            }
        }
        
        try:
            requests.post(FEISHU_WEBHOOK, json=payload)
        except Exception as e:
            logging.error(f"Failed to send webhook: {e}")

# Global Instance
dm = DataManager()
