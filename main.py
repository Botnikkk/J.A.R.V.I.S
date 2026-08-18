import sys
import subprocess
import os
import time
import random
from collections import defaultdict
from dotenv import load_dotenv

from scraper import InstagramScraper
from analyzer import ChatAnalyzer
from message_store import MessageStore
from trivia import TriviaManager
from fun_commands import (
    extract_user_ids_from_command,
    format_vs,
    format_roast,
    format_random,
)

def export_messages_to_files(messages, user_mapping, folder_name="messages"):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    user_texts = defaultdict(list)
    sorted_msgs = sorted(messages, key=lambda x: x.timestamp)

    for msg in sorted_msgs:
        if getattr(msg, 'text', None):
            formatted_time = msg.timestamp.strftime("%I:%M %p %d/%m/%Y")
            message_line = f"[{formatted_time}] {msg.text}"
            user_texts[str(msg.user_id)].append(message_line)

    for user_id, lines in user_texts.items():
        username = user_mapping.get(str(user_id), f"Unknown_User_{user_id}")
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-'))
        file_path = os.path.join(folder_name, f"{safe_username}_{user_id}.txt")

        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + "\n")

def find_new_messages(messages, last_processed_id):
    if last_processed_id is None:
        return []
    new_batch = []
    for msg in messages:
        msg_id = getattr(msg, 'id', None)
        if msg_id == last_processed_id:
            break
        new_batch.append(msg)
    new_batch.reverse()
    return new_batch

def detect_command(text, sender_id, owner_user_id):
    t = (text or "").lower()
    tokens = [tok.strip(",.!?:;") for tok in t.split()]
    
    if 'jarvis' not in tokens:
        return None
        
    if str(sender_id) != str(owner_user_id):
        chance = random.randint(0, 50)
        if chance == 6:
            return "chance"
            
    if "update" in tokens and str(sender_id) == str(owner_user_id):
        return "update"
    if "analytics" in tokens:
        return "analytics"
    if "vs" in tokens:
        return "vs"
    if "roast" in tokens:
        return "roast"
    if "random" in tokens:
        return "random"
    if "whosaidit" in tokens:
        return "whosaidit"
    if "answer" in tokens:
        return "answer"
        
    return None
    
def pick_command_to_run(new_batch, owner_user_id):
    candidates = []
    for msg in new_batch:
        text = getattr(msg, 'text', "") or ""
        cmd = detect_command(text, msg.user_id, owner_user_id)
        if cmd:
            candidates.append((msg, cmd))

    if not candidates:
        return None, None

    if owner_user_id:
        for msg, cmd in candidates:
            if str(msg.user_id) == str(owner_user_id):
                return msg, cmd

    return candidates[0]

def build_analytics_text(full_messages, user_mapping, timeout_minutes):
    analyzer = ChatAnalyzer(full_messages)
    most_active = analyzer.get_most_active()
    most_ignored = analyzer.get_most_ignored(timeout_minutes=timeout_minutes)

    text = "📊 INSTAGRAM GC ANALYTICS 📊\n"
    text += f"Analyzed {len(full_messages)} logged messages.\n\n"

    text += "🏆 MOST ACTIVE:\n"
    for user_id, count in most_active[:5]:
        username = user_mapping.get(str(user_id), f"Unknown_{user_id}")
        text += f" - {username}: {count} messages\n"

    text += "\n👻 MOST IGNORED:\n"
    for user_id, count in most_ignored[:5]:
        username = user_mapping.get(str(user_id), f"Unknown_{user_id}")
        text += f" - {username}: {count} times left on read\n"

    return text

def build_vs_text(full_messages, user_mapping, command_text):
    ids = extract_user_ids_from_command(command_text, "vs", user_mapping, max_users=2)
    if len(ids) < 2:
        return "⚠️ Couldn't find two users to compare. Grow a brain and actually tag a real person"

    analyzer = ChatAnalyzer(full_messages)
    stats1 = analyzer.get_user_stats(ids[0])
    stats2 = analyzer.get_user_stats(ids[1])
    name1 = user_mapping.get(ids[0], ids[0])
    name2 = user_mapping.get(ids[1], ids[1])

    if not stats1 or not stats2:
        missing = name1 if not stats1 else name2
        return f"⚠️ No logged messages for {missing} yet."

    return format_vs(name1, stats1, name2, stats2)

def build_roast_text(full_messages, user_mapping, command_text, owner_user_id, timezone_offset_hours=0):
    ids = extract_user_ids_from_command(command_text, "roast", user_mapping, max_users=1)
    
    if not ids:
        return "⚠️ Couldn't find who to roast. Grow a brain and actually tag a real person"
        
    if owner_user_id and str(ids[0]) == str(owner_user_id):
        return "Sorry i can't roast the person who controls my existence."
        
    analyzer = ChatAnalyzer(full_messages)
    stats = analyzer.get_user_stats(ids[0], timezone_offset_hours=timezone_offset_hours)
    name = user_mapping.get(ids[0], ids[0])
    
    if not stats:
        return f"⚠️ No logged messages for {name} yet."

    return format_roast(name, stats)

def build_random_text(full_messages, user_mapping):
    analyzer = ChatAnalyzer(full_messages)
    msg = analyzer.get_random_message()
    
    while msg and any(kw in (msg.text or "") for kw in ["jarvis", "Jarvis"]):
        msg = analyzer.get_random_message()
        
    if not msg:
        return "⚠️ No messages logged yet."
    username = user_mapping.get(str(msg.user_id), "someone")
    return format_random(username, msg)

def main():
    load_dotenv()

    TARGET_GC_NAME = os.getenv("TARGET_GC_NAME")
    TIMEOUT_MINUTES = int(os.getenv("TIMEOUT_MINUTES", 20))
    POLL_FETCH_SIZE = int(os.getenv("POLL_FETCH_SIZE", 5))
    CATCHUP_LIMIT = int(os.getenv("CATCHUP_LIMIT", 5000))
    OWNER_USER_ID = os.getenv("OWNER_USER_ID", "").strip() or None
    COMMAND_COOLDOWN_SECONDS = float(os.getenv("COMMAND_COOLDOWN_SECONDS", 1.5))
    TIMEZONE_OFFSET_HOURS = int(os.getenv("TIMEZONE_OFFSET_HOURS", 0))

    if not OWNER_USER_ID:
        print("⚠️ Warning: OWNER_USER_ID is not set — no one will be prioritized.")

    scraper = InstagramScraper()
    store = MessageStore()
    trivia = TriviaManager()

    try:
        print("Loading trusted session settings...")
        scraper.cl.load_settings("settings.json")
        print("Disguise loaded successfully.")
    except Exception as e:
        print(f"Login/Settings Error: {e}")
        return

    bot_user_id = str(scraper.cl.user_id)

    print(f"Catching up on message history (already logged: {len(store.seen_ids)})...")
    try:
        catchup_messages, user_mapping, thread_id = scraper.get_group_chat_data(TARGET_GC_NAME, limit=CATCHUP_LIMIT)
        added = store.append_new(catchup_messages, user_mapping, exclude_user_id=bot_user_id)
        print(f"Catch-up complete: {added} new message(s) logged. Total: {len(store.seen_ids)}\n")
    except Exception as e:
        print(f"Catch-up fetch failed: {e} — continuing with normal polling.\n")

    print("="*50)
    print("🤖 JARVIS — INSTAGRAM GC BOT ACTIVE 🤖")
    print("="*50)
    print(f"Target Group Chat: '{TARGET_GC_NAME}'")
    print("Polling every 1.5 seconds...")
    scraper.send_message(thread_id, "🤖 J.A.R.V.I.S online.")

    last_processed_message_id = None
    last_command_time = 0.0

    while True:
        try:
            messages, user_mapping, thread_id = scraper.get_group_chat_data(
                TARGET_GC_NAME, limit=POLL_FETCH_SIZE
            )

            new_count = store.append_new(messages, user_mapping, exclude_user_id=bot_user_id)
            if new_count:
                print(f"Stored {new_count} new message(s). Total logged: {len(store.seen_ids)}", end="\r", flush=True)

            if messages:
                new_batch = find_new_messages(messages, last_processed_message_id)

                # TRIVIA CHECK
                if trivia.active_trivia:
                    for msg in new_batch:
                        if str(msg.user_id) == bot_user_id:
                            continue
                        text = getattr(msg, 'text', '')
                        
                        if trivia.check_guess(text):
                            ans_name = trivia.active_trivia['author_name']
                            ans_hint = trivia.active_trivia['hint']
                            winner_name = user_mapping.get(str(msg.user_id), "Someone")
                            
                            win_text = f"🎉 CORRECT! {winner_name} got it right.\n\nIt was indeed @{ans_name} (sent in {ans_hint})."
                            scraper.send_message(thread_id, win_text, reply_to_message=msg)
                            
                            try:
                                scraper.cl.direct_send_reaction(thread_id, msg.id, "⭐")
                            except Exception as e:
                                print(f"Could not react: {e}")
                                
                            trivia.active_trivia = None
                            break

                # COMMAND DETECTION
                command_msg, command_type = pick_command_to_run(new_batch, OWNER_USER_ID)

                latest_id = getattr(messages[0], 'id', None)
                if latest_id:
                    last_processed_message_id = latest_id

                # COMMAND EXECUTION
                if command_msg:
                    now = time.time()
                    time_since_last = now - last_command_time

                    if time_since_last < COMMAND_COOLDOWN_SECONDS:
                        pass
                    else:
                        last_command_time = now
                        print(f"\nCommand Triggered: '{command_type}' by {user_mapping.get(str(command_msg.user_id))}")

                        full_messages = store.load_all(exclude_user_id=bot_user_id)

                        if command_type == "analytics":
                            export_messages_to_files(full_messages, user_mapping)
                            reply_text = build_analytics_text(full_messages, user_mapping, TIMEOUT_MINUTES)
                        elif command_type == "vs":
                            reply_text = build_vs_text(full_messages, user_mapping, command_msg.text)
                        elif command_type == "roast":
                            reply_text = build_roast_text(full_messages, user_mapping, command_msg.text, OWNER_USER_ID, timezone_offset_hours=TIMEZONE_OFFSET_HOURS)
                        elif command_type == "random":
                            reply_text = build_random_text(full_messages, user_mapping)
                        elif command_type == "whosaidit":
                            analyzer = ChatAnalyzer(full_messages)
                            quote_data = analyzer.get_whosaidit_quote(min_words=5)
                            
                            if quote_data:
                                reply_text = trivia.start_game(quote_data, user_mapping)
                            else:
                                reply_text = "⚠️ Everyone here is too boring. I couldn't find a good quote."
                        elif command_type == "answer":
                            reply_text = trivia.get_answer()
                        elif command_type == "update":
                            scraper.send_message(thread_id, "🔄 Pulling latest code from GitHub and restarting...")
                            try:
                                subprocess.run(["git", "pull"], check=True)
                                os.execv(sys.executable, ['python'] + sys.argv)    
                            except Exception as e:
                                scraper.send_message(thread_id, f"⚠️ Update failed: {e}")
                                reply_text = None
                        elif command_type == "chance":
                            reply_text = "Maa chuda mood nahi hai"
                        else:
                            reply_text = None

                        if reply_text:
                            scraper.send_message(thread_id, reply_text, reply_to_message=command_msg)
                        print("💤 Resuming background watch loop...")

        except Exception as e:
            print(f"\nPolling Warning: {e} - retrying in 3 seconds...")

        time.sleep(1.5)

if __name__ == "__main__":
    main()