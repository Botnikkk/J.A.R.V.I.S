import time
import random

class PassiveBehaviors:
    def __init__(self):
        self.sleep_tracker = {}
        self.last_print_time = time.time() # <-- Internal stopwatch for printing

        self.sleep_keywords = [
            "gn", "goodnight", "good night", "goognait", "goog nait",
            "so rha", "so raha", "sone jara", "so rhi", "so rha", "sone jari", 
            "going to sleep", "gud night", "gud nait",
            "gonna sleep", "gonna eep", "sone ja rha", "sone ja rhi",
            "nini time", "nini tame", "nini tem",
            "ninu time", "ninu tame", "ninu tem",
            "ninni time", "ninni tame", "ninni tem",
        ]

        # Different ways JARVIS can call someone out
        self.hypocrite_responses = [
            "soja @{username} bhdve",
            "@{username} acha lode aise so rha h",
            "@{username} go back to sleep nga",
            "koi to lundka (@{username}) sone ja rha tha",
            "{minutes}mins pehle sone rha tha @{username}",
            "@{username} lasted {minutes} without phone",
            "bhagwan ke liye soja @{username}"
        ]

    def check_hypocrite(self, new_batch, user_mapping):
        """Scans new messages for hypocrites and returns a list of callout texts."""
        callouts = []
        now = time.time()

        for msg in new_batch:
            user_id = str(msg.user_id)
            text = getattr(msg, 'text', '') or ""
            text_lower = text.lower()
            username = user_mapping.get(user_id, "Someone")

            # 1. THE TRAP SPRINGS: Are they supposed to be offline?
            if user_id in self.sleep_tracker:
                time_asleep = now - self.sleep_tracker[user_id]

                if time_asleep < 300:
                    # UNDER 5 MINUTES: They are still yapping right after saying goodnight.
                    pass 
                
                elif 300 <= time_asleep < 10800:
                    # BETWEEN 5 MINS AND 3 HOURS: The trap springs. Roast them.
                    minutes = int(time_asleep // 60)
                    template = random.choice(self.hypocrite_responses)
                    callouts.append(template.format(username=username, minutes=minutes))
                    
                    # Roast delivered, NOW we remove them from the tracker
                    del self.sleep_tracker[user_id]
                    print(f"🎯 [TRAP SPRUNG] Roasted {username} after {minutes} min. Removed from tracker.")
                
                else:
                    # OVER 3 HOURS: They actually slept and woke up. Remove silently.
                    del self.sleep_tracker[user_id]
                    print(f"🌅 [TRAP EXPIRED] {username} woke up legitimately. Removed from tracker.")

            # 2. THE TRAP IS SET: Are they announcing their departure?
            if any(kw in text_lower for kw in self.sleep_keywords):
                # We only trap them if the message is short (under 10 words)
                if len(text_lower.split()) <= 10:
                    self.sleep_tracker[user_id] = now
                    
                    tracked_names = [user_mapping.get(uid, uid) for uid in self.sleep_tracker.keys()]
                    print(f"🛌 [SLEEP TRAP SET/RESET] {username} went to sleep. Currently tracking: {tracked_names}")

        return callouts

    def print_watchlist(self, user_mapping):
        """Prints the currently tracked users exactly once every 60 seconds."""
        now = time.time()
        # If 60 seconds have passed since the last print
        if now - self.last_print_time >= 60:
            if self.sleep_tracker:  # Only print if there is actually someone in the list
                tracked_names = [user_mapping.get(uid, uid) for uid in self.sleep_tracker.keys()]
                print(f"🕒 [WATCHLIST] Currently monitoring: {tracked_names}")
            
            # Reset the stopwatch
            self.last_print_time = now