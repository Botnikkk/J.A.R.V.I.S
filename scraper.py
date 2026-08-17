import os
from instagrapi import Client

class InstagramScraper:
    def __init__(self, session_id):
        self.cl = Client()
        self.session_id = session_id

    def login(self):
        print("Injecting session cookie...")
        self.cl.login_by_sessionid(self.session_id)
        print("Bypassed login screen successfully.")

    def get_group_chat_data(self, gc_name, limit=500):
        """Finds the GC, extracts usernames, and downloads message history."""
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
        return messages, user_mapping, target_thread.id

    def send_message(self, thread_id, text, reply_to_message=None):
        """Sends a text message to the group chat. If reply_to_message is
        provided (a DirectMessage object), sends it as a threaded reply
        to that message instead of a standalone message."""
        self.cl.direct_send(text, thread_ids=[thread_id], reply_to_message=reply_to_message)
        print("✅ Message sent successfully!\n")