import time
import random


class PassiveBehaviors:
    def __init__(self):
        self.sleep_tracker = {}

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

                # If they text again between 5 minutes and 3 hours later
                if 300 < time_asleep < 10800:
                    minutes = int(time_asleep // 60)

                    # Pick a random roast template and fill in the blanks
                    template = random.choice(self.hypocrite_responses)
                    callouts.append(template.format(
                        username=username, minutes=minutes))

                # They spoke, so we remove them from the tracker
                del self.sleep_tracker[user_id]

            # 2. THE TRAP IS SET: Are they announcing their departure?
            if any(kw in text_lower for kw in self.sleep_keywords):
                # We only trap them if the message is short (under 6 words)
                if len(text_lower.split()) <= 10:
                    self.sleep_tracker[user_id] = now

        return callouts
