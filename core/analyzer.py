import random
import re
from collections import Counter
from datetime import timedelta, timezone

def _ensure_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

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
        sorted_msgs = sorted(self.messages, key=lambda x: _ensure_utc(x.timestamp))
        max_gap = timedelta(0)
        for i in range(len(sorted_msgs) - 1):
            current_msg = sorted_msgs[i]
            next_msg = sorted_msgs[i+1]
            time_gap = _ensure_utc(next_msg.timestamp) - _ensure_utc(current_msg.timestamp)
            if time_gap > max_gap:
                max_gap = time_gap
            if time_gap > timedelta(minutes=timeout_minutes):
                if current_msg.user_id != next_msg.user_id:
                    ignored_counts[current_msg.user_id] += 1
        return ignored_counts.most_common()

    def get_user_stats(self, user_id, timeout_minutes=20, timezone_offset_hours=0):
        user_id = str(user_id)
        user_msgs = [m for m in self.messages if str(m.user_id) == user_id]
        if not user_msgs:
            return None
        sorted_all = sorted(self.messages, key=lambda x: _ensure_utc(x.timestamp))
        total = len(user_msgs)
        word_counts = [len(m.text.split()) for m in user_msgs if m.text]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        longest = max(user_msgs, key=lambda m: len(m.text or ""))
        longest_message_length = len(longest.text or "")
        one_word_count = sum(1 for wc in word_counts if wc == 1)
        one_word_pct = (one_word_count / len(word_counts) * 100) if word_counts else 0
        caps_eligible = [m for m in user_msgs if m.text and len(m.text) >= 4]
        caps_count = sum(
            1 for m in caps_eligible
            if sum(c.isupper() for c in m.text if c.isalpha()) > sum(c.islower() for c in m.text if c.isalpha())
        )
        caps_pct = (caps_count / len(caps_eligible) * 100) if caps_eligible else 0
        question_count = sum(1 for m in user_msgs if m.text and m.text.strip().endswith("?"))
        question_pct = (question_count / total * 100) if total else 0
        exclaim_count = sum(1 for m in user_msgs if m.text and "!" in m.text)
        exclaim_pct = (exclaim_count / total * 100) if total else 0

        def local_hour(ts):
            # Always normalize to UTC first (consistent with the rest of
            # this file's naive/aware handling), then apply the configurable
            # offset — using ts.astimezone() directly here would silently
            # mis-handle the naive entries in the log.
            return (_ensure_utc(ts).hour + timezone_offset_hours) % 24

        night_owl_count = sum(1 for m in user_msgs if local_hour(m.timestamp) in (0, 1, 2, 3, 4))
        night_owl_pct = (night_owl_count / total * 100) if total else 0
        early_bird_count = sum(1 for m in user_msgs if local_hour(m.timestamp) in (5, 6, 7, 8))
        early_bird_pct = (early_bird_count / total * 100) if total else 0
        weekend_count = sum(1 for m in user_msgs if m.timestamp.weekday() >= 5)
        weekend_pct = (weekend_count / total * 100) if total else 0

        response_gaps = []
        for i in range(1, len(sorted_all)):
            prev_msg = sorted_all[i - 1]
            cur_msg = sorted_all[i]
            if str(cur_msg.user_id) == user_id and str(prev_msg.user_id) != user_id:
                gap = (_ensure_utc(cur_msg.timestamp) - _ensure_utc(prev_msg.timestamp)).total_seconds()
                if gap >= 0:
                    response_gaps.append(gap)
        avg_response_seconds = sum(response_gaps) / len(response_gaps) if response_gaps else None

        double_text_count = 0
        for i in range(1, len(sorted_all)):
            if str(sorted_all[i].user_id) == user_id and str(sorted_all[i - 1].user_id) == user_id:
                double_text_count += 1
        double_text_pct = (double_text_count / total * 100) if total else 0

        conversation_starts = 0
        for i in range(1, len(sorted_all)):
            gap = _ensure_utc(sorted_all[i].timestamp) - _ensure_utc(sorted_all[i - 1].timestamp)
            if gap > timedelta(minutes=timeout_minutes) and str(sorted_all[i].user_id) == user_id:
                conversation_starts += 1

        all_words = []
        for m in user_msgs:
            if m.text:
                all_words.extend(re.findall(r"[a-zA-Z']+", m.text.lower()))
        vocab_richness = (len(set(all_words)) / len(all_words)) if len(all_words) >= 20 else None
        total_word_count = len(all_words)

        return {
            "user_id": user_id, "message_count": total, "avg_words": avg_words,
            "longest_message": longest.text, "longest_message_length": longest_message_length,
            "one_word_pct": one_word_pct, "caps_pct": caps_pct, "question_pct": question_pct,
            "exclaim_pct": exclaim_pct, "night_owl_pct": night_owl_pct, "early_bird_pct": early_bird_pct,
            "weekend_pct": weekend_pct, "avg_response_seconds": avg_response_seconds,
            "double_text_pct": double_text_pct, "conversation_starts": conversation_starts,
            "vocab_richness": vocab_richness, "total_word_count": total_word_count,
        }

    def get_random_message(self):
        candidates = [m for m in self.messages if getattr(m, "text", None)]
        if not candidates:
            return None
        unique_users = list(set(m.user_id for m in candidates))
        if not unique_users:
            return None
        chosen_user = random.choice(unique_users)
        user_messages = [m for m in candidates if m.user_id == chosen_user]
        return random.choice(user_messages)

    def get_whosaidit_quote(self, min_words=5):
        candidates = []
        for m in self.messages:
            text = getattr(m, "text", "")
            if not text:
                continue
            text = text.strip()
            if len(text.split()) < min_words:
                continue
            if "http://" in text or "https://" in text or "www." in text:
                continue
            if text.startswith(("/", "!", "?", ".")):
                continue
            candidates.append(m)
        if not candidates:
            return None
        chosen = random.choice(candidates)
        return {
            "text": chosen.text,
            "author_id": chosen.user_id,
            "date_hint": chosen.timestamp.strftime("%B %Y")
        }

    def get_contextless_messages(self, msg_type="convo"):
        """Fetches smart, random messages for the convo and qna commands."""
        valid_msgs = []
        for m in self.messages:
            text = getattr(m, "text", "")
            if not text:
                continue
            text_lower = text.lower()
            if "jarvis" in text_lower:
                continue
            if "http" in text_lower or "www." in text_lower:
                continue
            if len(text.split()) < 2:
                continue
            valid_msgs.append(m)

        if not valid_msgs:
            return None

        if msg_type == "convo":
            users = list(set(m.user_id for m in valid_msgs))
            if len(users) < 2:
                return None

            num_participants = random.choice([2, 3]) if len(users) >= 3 else 2
            chosen_users = random.sample(users, num_participants)

            convo = []
            for uid in chosen_users:
                user_msgs = [m for m in valid_msgs if m.user_id == uid]
                convo.append(random.choice(user_msgs))
            return convo

        elif msg_type == "qna":
            questions = [m for m in valid_msgs if "?" in m.text]
            if not questions:
                return None
            chosen_q = random.choice(questions)

            answers = [m for m in valid_msgs if m.user_id != chosen_q.user_id and "?" not in m.text]
            if not answers:
                return None
            chosen_a = random.choice(answers)

            return [chosen_q, chosen_a]