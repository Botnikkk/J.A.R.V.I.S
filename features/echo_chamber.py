import re
import random
import math
from datetime import timezone
from collections import defaultdict, Counter

# UPGRADE 1: Added Hindi/Hinglish filler words
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "in",
    "on", "at", "it", "i", "you", "we", "he", "she", "they", "this", "that",
    "jarvis", "hai", "ho", "tu", "tha", "thi", "ki", "ko", "se", "aur", 
    "ye", "wo", "toh", "ka", "ke", "ne", "hi", "bhi", "kya", "me"
}

REPORTING_VERBS = {
    "said", "asked", "told", "mentioned", "wrote", "texted", "posted",
    "says", "asks", "tells", "claimed", "replied",
}

COMMAND_PREFIXES = ("!", "/", ".")


def _ensure_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text):
    return [w for w in _normalize(text).split() if w not in STOPWORDS and len(w) > 1]


def _looks_like_command(text):
    """
    Checks if a message is addressed to a bot rather than the group.
    Filters out prefix commands AND anything starting with 'jarvis'.
    """
    t = text.lower().strip()
    if t.startswith(COMMAND_PREFIXES):
        return True
    if t.startswith("jarvis"):
        return True
    return False


class EchoChamber:
    def __init__(self, messages):
        self.messages = sorted(messages, key=lambda m: _ensure_utc(m.timestamp))
        self._build_index()

    def _build_index(self):
        self.word_index = defaultdict(set)
        self.tokens_by_pos = {}
        word_doc_freq = Counter()

        for i, msg in enumerate(self.messages):
            text = getattr(msg, "text", None)
            if not text:
                continue
            tokens = _tokenize(text)
            self.tokens_by_pos[i] = tokens
            
            unique_tokens = set(tokens)
            for w in unique_tokens:
                word_doc_freq[w] += 1
                self.word_index[w].add(i)

        total_docs = len(self.messages)
        self.idf = {}
        for w, df in word_doc_freq.items():
            self.idf[w] = math.log(total_docs / (1 + df))

    def _similarity(self, trigger_tokens, trigger_text, original_tokens, original_text):
        if not trigger_tokens or not original_tokens:
            return 0.0
            
        trigger_set = set(trigger_tokens)
        original_set = set(original_tokens)
        overlap = trigger_set & original_set
        
        if not overlap:
            return 0.0
            
        # UPGRADE 2: Recall vs. Precision Balancing
        # Penalizes matching a 2-word trigger to a 20-word historical paragraph.
        trigger_idf = sum(self.idf.get(w, 1.0) for w in trigger_set)
        overlap_idf = sum(self.idf.get(w, 1.0) for w in overlap)
        original_idf = sum(self.idf.get(w, 1.0) for w in original_set)
        
        recall = overlap_idf / trigger_idf if trigger_idf else 0
        precision = overlap_idf / original_idf if original_idf else 0
        
        # Heavily weigh recall (we want to cover the prompt) but factor in precision
        base_score = (0.75 * recall) + (0.25 * precision)
        
        clean_trigger = re.sub(r"[^\w\s]", "", trigger_text.lower()).strip()
        clean_original = re.sub(r"[^\w\s]", "", original_text.lower()).strip()
        if clean_trigger and clean_trigger in clean_original:
            base_score *= 1.5  
            
        return base_score

    def _search(self, trigger_tokens, trigger_text, max_reply_gap_seconds):
        """
        Core matching routine, operating on a fixed set of trigger tokens.
        Returns a result dict, or None if nothing cleared the bar.
        """
        trigger_is_question = "?" in trigger_text
        candidate_positions = set()

        for w in trigger_tokens:
            candidate_positions |= self.word_index.get(w, set())

        if not candidate_positions:
            return None

        valid_replies = []

        for pos in candidate_positions:
            if pos + 1 >= len(self.messages):
                continue

            original_msg = self.messages[pos]
            reply_msg = self.messages[pos+1]
            original_tokens = self.tokens_by_pos.get(pos, [])
            original_text = getattr(original_msg, "text", "") or ""

            # Skips the source if it was a command or addressed to JARVIS
            if _looks_like_command(original_text):
                continue

            if str(reply_msg.user_id) == str(original_msg.user_id):
                continue

            sim_score = self._similarity(trigger_tokens, trigger_text, original_tokens, original_text)
            if sim_score < 0.4:  # Raised base threshold
                continue

            reply_text = getattr(reply_msg, "text", None)
            if not reply_text:
                continue

            # Skips the reply if it was a command or addressed to JARVIS
            if _looks_like_command(reply_text):
                continue

            # UPGRADE 3: The Cross-Talk Tagging Filter
            if "@" in reply_text and "@" not in trigger_text:
                continue

            low_reply = reply_text.lower()
            if "http" in low_reply or ".com" in low_reply:
                continue

            reply_word_count = len(reply_text.split())
            if reply_word_count > 15:
                continue

            if trigger_is_question and "?" in reply_text:
                sim_score *= 0.5
            elif not trigger_is_question and "?" in reply_text:
                sim_score *= 1.2

            gap = (_ensure_utc(reply_msg.timestamp) - _ensure_utc(original_msg.timestamp)).total_seconds()
            if gap < 0 or gap > max_reply_gap_seconds:
                continue

            # Massive bonus for rapid-fire replies (proves it wasn't cross-talk)
            if gap <= 15:
                sim_score += 0.5
            elif gap <= 45:
                sim_score += 0.2

            cluster_key = _normalize(reply_text)
            if not cluster_key:
                continue

            valid_replies.append({
                "anchor_score": sim_score,
                "cluster_key": cluster_key,
                "raw_reply": reply_text,
                "matched_anchor": original_text
            })

        if not valid_replies:
            return None

        clusters = defaultdict(list)
        for r in valid_replies:
            clusters[r["cluster_key"]].append(r)

        cluster_scores = []
        for key, replies in clusters.items():
            freq = len(replies)
            avg_anchor_score = sum(r["anchor_score"] for r in replies) / freq

            # UPGRADE 4: True Consensus Weighting
            consensus_score = avg_anchor_score + ((freq - 1) * 1.5)

            best_reply_obj = max(replies, key=lambda x: x["anchor_score"])

            cluster_scores.append({
                "score": consensus_score,
                "freq": freq,
                "reply_text": best_reply_obj["raw_reply"],
                "matched_source_text": best_reply_obj["matched_anchor"]
            })

        cluster_scores.sort(key=lambda x: x["score"], reverse=True)

        # UPGRADE 5: The "Ghosting" Rule
        if cluster_scores[0]["score"] < 2.0:
            return None

        top_candidates = cluster_scores[:3]
        safe_candidates = [c for c in top_candidates if c["score"] >= 2.0]

        return random.choice(safe_candidates)

    def _drop_weakest_token(self, trigger_tokens):
        """
        Removes the single least-informative token from trigger_tokens,
        so the words most likely to be distinctive are the ones kept
        the longest as we relax the search.

        Words that never appear anywhere in the message history (out of
        vocabulary) are dropped first — they contribute zero candidates
        and only dilute the similarity score. Only once every remaining
        token is "known" do we fall back to dropping the lowest-IDF
        (most common/least distinctive) known token.
        """
        unseen = [w for w in trigger_tokens if w not in self.idf]
        if unseen:
            weakest = unseen[0]
        else:
            weakest = min(trigger_tokens, key=lambda w: self.idf[w])
        remaining = trigger_tokens[:]
        remaining.remove(weakest)
        return remaining

    def find_echo(self, trigger_text, now_timestamp, max_reply_gap_seconds=300, min_trigger_tokens=1):
        trigger_tokens = _tokenize(trigger_text)
        if len(trigger_tokens) < min_trigger_tokens:
            print(f"[EchoChamber] '{trigger_text}' -> fewer than {min_trigger_tokens} usable keyword(s), skipping search. Reacting instead.")
            return None

        # Progressive fallback: search with the full keyword list, and if
        # nothing matches, drop the weakest (lowest-IDF) keyword and try
        # again, repeating until either a match is found or we run out
        # of keywords entirely.
        attempt = 1
        while trigger_tokens:
            print(f"[EchoChamber] attempt {attempt}: matching on keywords {trigger_tokens}")
            result = self._search(trigger_tokens, trigger_text, max_reply_gap_seconds)
            if result is not None:
                print(f"[EchoChamber] match found on attempt {attempt} with keywords {trigger_tokens}")
                return result

            if len(trigger_tokens) == 1:
                break
            trigger_tokens = self._drop_weakest_token(trigger_tokens)
            attempt += 1

        print(f"[EchoChamber] no match found after exhausting all keywords for '{trigger_text}'. Reacting instead.")
        return None


_cache = {"chamber": None, "count": 0}

def get_or_build_echo_chamber(full_messages):
    if _cache["chamber"] is None or _cache["count"] != len(full_messages):
        _cache["chamber"] = EchoChamber(full_messages)
        _cache["count"] = len(full_messages)
    return _cache["chamber"]