# learning_engine.py
import random
import time
from data_manager import dm
from config import WORDS_PER_SESSION, REVIEW_INTERVALS

class LearningEngine:
    def __init__(self):
        self.session_words = []
        self.current_index = 0
        self.mastery_map = {} # {word_id: correct_streak}
        self.wrong_history = {} # {word_id: times_wrong}
        self.session_type = "new" # "new" or "review"
        
    def start_new_session(self, count=WORDS_PER_SESSION):
        self.session_type = "new"
        words = dm.get_new_words(limit=count)
        self._init_session(words)
        return len(words)

    def start_review_session(self, count=None): # Changed to None for unlimited
        self.session_type = "review"
        words = dm.get_review_words(limit=count)
        self._init_session(words)
        return len(words)
        
    def _init_session(self, words):
        self.session_words = words
        self.mastery_map = {w['id']: 0 for w in words}
        self.wrong_history = {w['id']: 0 for w in words}
        
    def get_next_question(self):
        """
        Determine the next question based on mastery status.
        - Mastery < 2: Word needs practice in this session.
        """
        unmastered = [w for w in self.session_words if self.mastery_map[w['id']] < 2]
        if not unmastered:
            return None # Session complete
            
        word = random.choice(unmastered)
        streak = self.mastery_map[word['id']]
        
        # Decide question type based on mastery level
        if streak == 0:
            q_type = random.choice(["choice", "matching"])
        else:
            q_type = random.choice(["spelling_easy", "spelling_hard"])
            
        return {
            "type": q_type,
            "word": word,
            "options": self._generate_options(word) if q_type in ["choice", "matching"] else None
        }
        
    def _generate_options(self, target_word, count=4):
        distrectors = [w for w in self.session_words if w['id'] != target_word['id']]
        if len(distrectors) < count - 1:
            options = distrectors + [target_word]
        else:
            options = random.sample(distrectors, count - 1) + [target_word]
        random.shuffle(options)
        return options

    def submit_answer(self, word_id, is_correct):
        """
        Update local session mastery and DEFER Feishu sync.
        Store pending updates to batch later for faster UI response.
        """
        word_obj = next((w for w in self.session_words if w['id'] == word_id), None)
        current_interval = word_obj.get('interval', 0) if word_obj else 0

        if is_correct:
            self.mastery_map[word_id] += 1
            # Queue update for later
            if self.mastery_map[word_id] >= 2:
                self._queue_update(word_id, True, current_interval)
        else:
            self.mastery_map[word_id] = 0
            self.wrong_history[word_id] += 1
            # Queue update for later
            self._queue_update(word_id, False, current_interval)
            
        return self.mastery_map[word_id] >= 2
    
    def _queue_update(self, word_id, is_correct, interval):
        """Store pending updates to process later"""
        if not hasattr(self, 'pending_updates'):
            self.pending_updates = []
        self.pending_updates.append({
            'word_id': word_id,
            'is_correct': is_correct,
            'interval': interval
        })
    
    def flush_pending_updates(self):
        """Process all pending updates to Feishu"""
        if not hasattr(self, 'pending_updates'):
            return
        for update in self.pending_updates:
            dm.update_word_progress(
                update['word_id'], 
                update['is_correct'], 
                update['interval']
            )
        self.pending_updates = []

# Global Engine
le = LearningEngine()
