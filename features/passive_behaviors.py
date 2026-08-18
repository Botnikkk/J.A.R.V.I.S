import time
import random

class PassiveBehaviors:
    # --- ADDED BOT ID AND IGNORED IDS TO INIT ---
    def __init__(self, bot_user_id, ignored_ids=None):
        self.bot_user_id = str(bot_user_id)
        self.ignored_ids = set(ignored_ids) if ignored_ids else set()
        
        self.sleep_tracker = {}
        self.last_print_time = time.time()

        self.sleep_keywords = [
            "gn", "goodnight", "good night", "goognait", "goog nait",
            "so rha", "so raha", "sone jara", "so rhi", "so rha", "sone jari", 
            "going to sleep", "gud night", "gud nait",
            "gonna sleep", "gonna eep", "sone ja rha", "sone ja rhi",
            "nini time", "nini tame", "nini tem",
            "ninu time", "ninu tame", "ninu tem",
            "ninni time", "ninni tame", "ninni tem",
        ]

        self.hypocrite_responses = [
            "soja @{username} bhdve",
            "@{username} acha lode aise so rha h",
            "@{username} go back to sleep nga",
            "koi to lundka (@{username}) sone ja rha tha",
            "{minutes}mins pehle sone ja rha tha @{username}",
            "@{username} lasted {minutes} without phone",
            "bhagwan ke liye soja @{username}"
        ]

    def check_hypocrite(self, new_batch, user_mapping):
        callouts = []
        now = time.time()

        for msg in new_batch:
            user_id = str(msg.user_id)
            
            # --- THE FIX: INSTANTLY SKIP THE BOT AND IGNORED ACCOUNTS ---
            if user_id == self.bot_user_id or user_id in self.ignored_ids:
                continue
            # -----------------------------------------------------------

            text = getattr(msg, 'text', '') or ""
            text_lower = text.lower()
            username = user_mapping.get(user_id, "Someone")

            # 1. THE TRAP SPRINGS
            if user_id in self.sleep_tracker:
                time_asleep = now - self.sleep_tracker[user_id]

                if time_asleep < 300:
                    pass 
                elif 300 <= time_asleep < 10800:
                    minutes = int(time_asleep // 60)
                    template = random.choice(self.hypocrite_responses)
                    callouts.append(template.format(username=username, minutes=minutes))
                    
                    del self.sleep_tracker[user_id]
                    print(f"🎯 [TRAP SPRUNG] Roasted {username} after {minutes} min. Removed from tracker.")
                else:
                    del self.sleep_tracker[user_id]
                    print(f"🌅 [TRAP EXPIRED] {username} woke up legitimately. Removed from tracker.")

            # 2. THE TRAP IS SET
            if any(kw in text_lower for kw in self.sleep_keywords):
                if len(text_lower.split()) <= 10:
                    self.sleep_tracker[user_id] = now
                    
                    tracked_names = [user_mapping.get(uid, uid) for uid in self.sleep_tracker.keys()]
                    print(f"🛌 [SLEEP TRAP SET/RESET] {username} went to sleep. Currently tracking: {tracked_names}")

        return callouts