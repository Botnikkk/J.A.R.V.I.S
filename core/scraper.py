import os
from instagrapi import Client

class InstagramScraper:
    def __init__(self, settings_path="settings.json"):
        self.cl = Client()
        self.settings_path = settings_path

    def login(self):
        """Applies a pre-authenticated session from settings.json directly —
        deliberately never calls cl.login() with a password, since repeated
        password auth attempts (even 'cheap' ones with valid cached cookies)
        can trigger Instagram's challenge/email-code flow. If this session
        has expired, you'll need to regenerate settings.json separately."""
        print("Loading trusted session settings...")

        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(
                f"{self.settings_path} not found. This bot expects a pre-authenticated "
                "session file — no username/password login is attempted."
            )

        settings = self.cl.load_settings(self.settings_path)
        self.cl.set_settings(settings)

        # login() normally sets this — restore it manually from the cookie
        # since we're intentionally skipping that call.
        if not self.cl.user_id:
            ds_user_id = self.cl.cookie_dict.get("ds_user_id")
            if ds_user_id:
                self.cl.user_id = int(ds_user_id)

        # Lightweight check to confirm the session is actually still valid —
        # catches an expired session here, at startup, instead of it failing
        # mysteriously on the first real API call mid-poll.
        try:
            self.cl.get_timeline_feed()
        except Exception as e:
            raise RuntimeError(
                f"settings.json loaded but the session looks invalid/expired ({e}). "
                "You'll need to regenerate settings.json from a fresh authenticated session."
            )

        print("Disguise loaded successfully. Ready to run!")

    def get_group_chat_data(self, gc_name, limit=500, ignored_ids=None):
        threads = self.cl.direct_threads(amount=20)
        target_thread = None

        for thread in threads:
            if getattr(thread, 'thread_title', None) == gc_name:
                target_thread = thread
                break

        if not target_thread:
            raise ValueError(f"Group chat '{gc_name}' not found in your recent inbox.")

        user_mapping = {}
        for user in target_thread.users:
            user_mapping[str(user.pk)] = user.username

        if self.cl.user_id:
            user_mapping[str(self.cl.user_id)] = "Bot_Account"

        messages = self.cl.direct_messages(target_thread.id, amount=limit)

        ignored_ids = ignored_ids or set()
        filtered_messages = [m for m in messages if str(m.user_id) not in ignored_ids]

        return filtered_messages, user_mapping, target_thread.id

    def send_message(self, thread_id, text, reply_to_message=None):
        """Sends a message to the chat, natively replying to a specific
        message if provided. instagrapi 2.18.16+ supports this directly."""
        try:
            if reply_to_message:
                message_id = getattr(reply_to_message, 'id', None)
                if message_id:
                    self.cl.direct_send(text, thread_ids=[int(thread_id)], reply_to_message=message_id)
                else:
                    self.cl.direct_send(text, thread_ids=[int(thread_id)])
            else:
                self.cl.direct_send(text, thread_ids=[int(thread_id)])
        except Exception as e:
            print(f"⚠️ Failed to send message: {e}")