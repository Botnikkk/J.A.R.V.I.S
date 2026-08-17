import random
import re
from collections import Counter
from datetime import timedelta

class ChatAnalyzer:
    def __init__(self, messages):
        self.messages = messages

    def get_most_active(self):
        message_counts = Counter()
        for msg in self.messages:
            message_counts[msg.user_id] += 1
        return message_counts.most_common()

    def get_most_ignored(self, timeout_minutes=20):
        ignored_counts = Counter()
        sorted_msgs = sorted(self.messages, key=lambda x: x.timestamp)
        max_gap = timedelta(0)

        for i in range(len(sorted_msgs) - 1):
            current_msg = sorted_msgs[i]
            next_msg = sorted_msgs[i+1]
            time_gap = next_msg.timestamp - current_msg.timestamp

            if time_gap > max_gap:
                max_gap = time_gap

            if time_gap > timedelta(minutes=timeout_minutes):
                if current_msg.user_id != next_msg.user_id:
                    ignored_counts[current_msg.user_id] += 1

        return ignored_counts.most_common()

    def get_user_stats(self, user_id, timeout_minutes=20, timezone_offset_hours=0):
        """Returns a stats dict for one user, or None if they have no messages.
        timezone_offset_hours shifts UTC timestamps for time-of-day buckets
        (night owl / early bird / weekend) — set to your local UTC offset
        for accurate results, defaults to 0 (UTC)."""
        user_id = str(user_id)
        user_msgs = [m for m in self.messages if str(m.user_id) == user_id]
        if not user_msgs:
            return None

        sorted_all = sorted(self.messages, key=lambda x: x.timestamp)
        total = len(user_msgs)

        # --- word / length stats ---
        word_counts = [len(m.text.split()) for m in user_msgs if m.text]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        longest = max(user_msgs, key=lambda m: len(m.text or ""))
        longest_message_length = len(longest.text or "")
        one_word_count = sum(1 for wc in word_counts if wc == 1)
        one_word_pct = (one_word_count / len(word_counts) * 100) if word_counts else 0

        # --- caps ---
        caps_eligible = [m for m in user_msgs if m.text and len(m.text) >= 4]
        caps_count = sum(
            1 for m in caps_eligible
            if sum(c.isupper() for c in m.text if c.isalpha()) > sum(c.islower() for c in m.text if c.isalpha())
        )
        caps_pct = (caps_count / len(caps_eligible) * 100) if caps_eligible else 0

        # --- punctuation habits ---
        question_count = sum(1 for m in user_msgs if m.text and m.text.strip().endswith("?"))
        question_pct = (question_count / total * 100) if total else 0
        exclaim_count = sum(1 for m in user_msgs if m.text and "!" in m.text)
        exclaim_pct = (exclaim_count / total * 100) if total else 0

        # --- time of day (shifted by timezone_offset_hours) ---
        def local_hour(ts):
            return (ts.hour + timezone_offset_hours) % 24

        night_owl_count = sum(1 for m in user_msgs if local_hour(m.timestamp) in (0, 1, 2, 3, 4))
        night_owl_pct = (night_owl_count / total * 100) if total else 0
        early_bird_count = sum(1 for m in user_msgs if local_hour(m.timestamp) in (5, 6, 7, 8))
        early_bird_pct = (early_bird_count / total * 100) if total else 0
        weekend_count = sum(1 for m in user_msgs if m.timestamp.weekday() >= 5)
        weekend_pct = (weekend_count / total * 100) if total else 0

        # --- response speed ---
        response_gaps = []
        for i in range(1, len(sorted_all)):
            prev_msg = sorted_all[i - 1]
            cur_msg = sorted_all[i]
            if str(cur_msg.user_id) == user_id and str(prev_msg.user_id) != user_id:
                gap = (cur_msg.timestamp - prev_msg.timestamp).total_seconds()
                if gap >= 0:
                    response_gaps.append(gap)
        avg_response_seconds = sum(response_gaps) / len(response_gaps) if response_gaps else None

        # --- double-texting: % of this user's messages that immediately
        # followed another message from the same user (no one replied between) ---
        double_text_count = 0
        for i in range(1, len(sorted_all)):
            if str(sorted_all[i].user_id) == user_id and str(sorted_all[i - 1].user_id) == user_id:
                double_text_count += 1
        double_text_pct = (double_text_count / total * 100) if total else 0

        # --- conversation starts: times this user sent the first message
        # after a gap longer than timeout_minutes ---
        conversation_starts = 0
        for i in range(1, len(sorted_all)):
            gap = sorted_all[i].timestamp - sorted_all[i - 1].timestamp
            if gap > timedelta(minutes=timeout_minutes) and str(sorted_all[i].user_id) == user_id:
                conversation_starts += 1

        # --- vocabulary richness: unique words / total words ---
        all_words = []
        for m in user_msgs:
            if m.text:
                all_words.extend(re.findall(r"[a-zA-Z']+", m.text.lower()))
        vocab_richness = (len(set(all_words)) / len(all_words)) if len(all_words) >= 20 else None
        total_word_count = len(all_words)

        return {
            "user_id": user_id,
            "message_count": total,
            "avg_words": avg_words,
            "longest_message": longest.text,
            "longest_message_length": longest_message_length,
            "one_word_pct": one_word_pct,
            "caps_pct": caps_pct,
            "question_pct": question_pct,
            "exclaim_pct": exclaim_pct,
            "night_owl_pct": night_owl_pct,
            "early_bird_pct": early_bird_pct,
            "weekend_pct": weekend_pct,
            "avg_response_seconds": avg_response_seconds,
            "double_text_pct": double_text_pct,
            "conversation_starts": conversation_starts,
            "vocab_richness": vocab_richness,
            "total_word_count": total_word_count,
        }

    def get_random_message(self):
        # Filter down to messages that actually have text
        candidates = [m for m in self.messages if getattr(m, "text", None)]
        if not candidates:
            return None
            
        # 1. Get all unique users who have sent at least one valid message
        unique_users = list(set(m.user_id for m in candidates))
        
        if not unique_users:
            return None
            
        # 2. Pick a random user so everyone has an equal chance
        chosen_user = random.choice(unique_users)
        
        # 3. Filter the candidates to only messages from the chosen user
        user_messages = [m for m in candidates if m.user_id == chosen_user]
        
        # 4. Return a random message from that specific user
        return random.choice(user_messages)
    def get_whosaidit_quote(self, min_words=5):
        """
        Picks a random, out-of-context message that is long enough to be 
        guessable, excluding links and bot commands.
        """
        candidates = []
        for m in self.messages:
            text = getattr(m, "text", "")
            if not text:
                continue
            
            text = text.strip()
            
            # Filter 1: Must be at least `min_words` long so it's an actual thought
            if len(text.split()) < min_words:
                continue
                
            # Filter 2: No links (nobody is guessing who sent a TikTok link)
            if "http://" in text or "https://" in text or "www." in text:
                continue
                
            # Filter 3: Ignore typical bot commands (modify these prefixes if needed)
            if text.startswith(("/", "!", "?", ".")):
                continue
                
            candidates.append(m)

        if not candidates:
            return None

        # Pick a random message
        chosen = random.choice(candidates)
        
        return {
            "text": chosen.text,
            "author_id": chosen.user_id,
            "date_hint": chosen.timestamp.strftime("%B %Y") # e.g., "November 2023" for a hint
        }