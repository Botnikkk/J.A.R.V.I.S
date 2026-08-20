import sys
import subprocess
import os
import time
import random
from collections import defaultdict
from dotenv import load_dotenv

from datetime import datetime, timezone, timedelta
from features.smalltalk import get_smalltalk_reply
from features.echo_chamber import get_or_build_echo_chamber
from utils.logger import log_jarvis_interaction
from core.scraper import InstagramScraper
from core.analyzer import ChatAnalyzer
from core.message_store import MessageStore
from features.trivia import TriviaManager
from features.passive_behaviors import PassiveBehaviors
from features.fun_commands import (
    extract_user_ids_from_command,
    format_vs,
    format_roast,
    format_random,
    format_convo,
    format_qna,
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
    if "convo" in tokens:
        return "convo"
    if "qna" in tokens:
        return "qna"
    if "whosaidit" in tokens:
        return "whosaidit"
    if "answer" in tokens:
        return "answer"

    return "echo"

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

def build_convo_text(full_messages, user_mapping):
    analyzer = ChatAnalyzer(full_messages)
    convo_msgs = analyzer.get_contextless_messages(msg_type="convo")
    if not convo_msgs:
        return "⚠️ Not enough valid messages to generate a conversation."
    return format_convo(convo_msgs, user_mapping)

def build_qna_text(full_messages, user_mapping):
    analyzer = ChatAnalyzer(full_messages)
    qna_msgs = analyzer.get_contextless_messages(msg_type="qna")
    if not qna_msgs:
        return "⚠️ Not enough valid questions/answers to generate a Q&A."
    return format_qna(qna_msgs, user_mapping)

def handle_circadian_sleep(scraper, thread_id, sleep_start_hour=2, wake_hour=8):
    now = datetime.now()
    if sleep_start_hour <= now.hour < wake_hour:
        wake_time = now.replace(hour=wake_hour, minute=0, second=0, microsecond=0)
        sleep_seconds = (wake_time - now).total_seconds()
        
        if sleep_seconds > 0:
            formatted_wake = wake_time.strftime("%I:%M %p")
            sleep_msg = f"😴 J.A.R.V.I.S is sleeping to maintain human hours. Offline until {formatted_wake}."
            print(f"\n{sleep_msg}")
            try:
                scraper.send_message(thread_id, sleep_msg)
            except Exception:
                pass
            
            time.sleep(sleep_seconds)
            
            wake_msg = "🌅 J.A.R.V.I.S awake and back online."
            print(f"\n{wake_msg}")
            try:
                scraper.send_message(thread_id, wake_msg)
            except Exception:
                pass

def simulate_feed_scroll(scraper, thread_id):
    # scrolls every ~5min
    if random.randint(1, 50) == 1:
        scroll_seconds = random.randint(30, 90)
        scroll_msg = f"📱 Scrolling the feed for {scroll_seconds}s to avoid bot detection. BRB."
        print(f"\n{scroll_msg}")
        
        try:
            scraper.send_message(thread_id, scroll_msg)
            scraper.cl.timeline_feed()
        except Exception as e:
            print(f"Scroll simulation error: {e}")
            
        time.sleep(scroll_seconds)
        
        try:
            scraper.send_message(thread_id, "👀 Back from Doom scrolling.")
        except Exception:
            pass

def main():
    load_dotenv()

    TARGET_GC_NAME = os.getenv("TARGET_GC_NAME")
    TIMEOUT_MINUTES = int(os.getenv("TIMEOUT_MINUTES", 20))
    POLL_FETCH_SIZE = int(os.getenv("POLL_FETCH_SIZE", 2))
    CATCHUP_LIMIT = int(os.getenv("CATCHUP_LIMIT", 100))
    OWNER_USER_ID = os.getenv("OWNER_USER_ID", "").strip() or None
    TIMEZONE_OFFSET_HOURS = int(os.getenv("TIMEZONE_OFFSET_HOURS", 5))
    ECHO_MAX_REPLY_GAP_SECONDS = float(os.getenv("ECHO_MAX_REPLY_GAP_SECONDS", 300))

    IGNORED_IDS = {"37797976551", "64528677628"}  # Meta AI + old bot

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
    passive = PassiveBehaviors(bot_user_id=bot_user_id, ignored_ids=IGNORED_IDS)

    try:
        _, _, thread_id = scraper.get_group_chat_data(TARGET_GC_NAME, limit=1, ignored_ids=IGNORED_IDS)
    except Exception as e:
        print(f"Fatal: couldn't resolve group chat thread: {e}")
        return

    print(f"Catching up on message history (already logged: {len(store.seen_ids)})...")
    try:
        catchup_messages, user_mapping, _ = scraper.get_group_chat_data(TARGET_GC_NAME, limit=CATCHUP_LIMIT, ignored_ids=IGNORED_IDS)
        added = store.append_new(catchup_messages, user_mapping, exclude_user_id=bot_user_id)
        print(f"Catch-up complete: {added} new message(s) logged. Total: {len(store.seen_ids)}\n")
    except Exception as e:
        print(f"Catch-up fetch failed: {e} — continuing with normal polling.\n")

    print("="*50)
    print("🤖 JARVIS — INSTAGRAM GC BOT ACTIVE 🤖")
    print("="*50)
    print(f"Target Group Chat: '{TARGET_GC_NAME}'")
    print("Polling active...")
    scraper.send_message(thread_id, "🤖 J.A.R.V.I.S online.")

    last_processed_message_id = None
    consecutive_errors = 0

    while True:
        try:
            # 1. Check Circadian Sleep Schedule (2 AM - 8 AM)
            handle_circadian_sleep(scraper, thread_id, sleep_start_hour=2, wake_hour=8)

            # 2. Random Feed Scroll Simulation
            simulate_feed_scroll(scraper, thread_id)

            # 3. Poll Group Chat Messages
            messages, user_mapping, thread_id = scraper.get_group_chat_data(
                TARGET_GC_NAME, limit=POLL_FETCH_SIZE, ignored_ids=IGNORED_IDS
            )

            new_count = store.append_new(messages, user_mapping, exclude_user_id=bot_user_id)
            if new_count:
                print(f"Stored {new_count} new message(s). Total logged: {len(store.seen_ids)}", end="\r", flush=True)

            if messages:
                new_batch = find_new_messages(messages, last_processed_message_id)

                callouts = passive.check_hypocrite(new_batch, user_mapping)
                for callout_text in callouts:
                    scraper.send_message(thread_id, callout_text)
                    print(f"💀 Hypocrite detected: {callout_text}")

                if trivia.active_trivia:
                    for msg in new_batch:
                        if str(msg.user_id) == bot_user_id:
                            continue
                        text = getattr(msg, 'text', '')
                        
                        matched_alias = trivia.check_guess(text)
                        
                        if matched_alias:
                            winner_name = user_mapping.get(str(msg.user_id), "Someone")
                            win_text = f"🎉 CORRECT! {winner_name} got it right.\n\nIt was indeed {matched_alias}."
                            scraper.send_message(thread_id, win_text, reply_to_message=msg)
                            
                            try:
                                scraper.cl.direct_send_reaction(thread_id, msg.id, "⭐")
                            except Exception as e:
                                print(f"Could not react: {e}")
                                
                            trivia.active_trivia = None
                            break

                command_msg, command_type = pick_command_to_run(new_batch, OWNER_USER_ID)

                latest_id = getattr(messages[0], 'id', None)
                if latest_id:
                    last_processed_message_id = latest_id

                if command_msg:
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
                    elif command_type == "convo":
                        reply_text = build_convo_text(full_messages, user_mapping)
                    elif command_type == "qna":
                        reply_text = build_qna_text(full_messages, user_mapping)
                    elif command_type == "whosaidit":
                        analyzerObj = ChatAnalyzer(full_messages)
                        reply_text = trivia.start_game(analyzerObj, user_mapping)
                        if not reply_text:
                            reply_text = "⚠️ Couldn't find a quote from a registered member in the database. Try again."
                    elif command_type == "answer":
                        reply_text = trivia.get_answer()
                    elif command_type == "update":
                        scraper.send_message(thread_id, "🔄 Pulling latest code from GitHub and restarting...")
                        try:
                            subprocess.run(["git", "pull"], check=True)
                            os.execv(sys.executable, ['python3'] + sys.argv)
                        except Exception as e:
                            scraper.send_message(thread_id, f"⚠️ Update failed: {e}")
                            reply_text = None
                    elif command_type == "chance":
                        reply_text = "Maa chuda mood nahi hai"
                    elif command_type == "echo":
                        username = user_mapping.get(str(command_msg.user_id), "Unknown")
                        prompt = command_msg.text
                        clean_prompt = " ".join([tok for tok in prompt.split() if tok.lower().strip(",.!?:;") != "jarvis"])
                        
                        smalltalk_reply = get_smalltalk_reply(clean_prompt)
                        if smalltalk_reply:
                            reply_text = smalltalk_reply
                            print(f"Smalltalk: matched -> \"{reply_text}\"")
                            log_jarvis_interaction(username, clean_prompt, "SMALLTALK", reply_text)
                        else:
                            chamber = get_or_build_echo_chamber(full_messages)
                            match = chamber.find_echo(
                                clean_prompt,
                                datetime.now(timezone.utc),
                                max_reply_gap_seconds=ECHO_MAX_REPLY_GAP_SECONDS,
                            )
                            if match:
                                reply_text = match["reply_text"]
                                print(f"Echo Chamber: MATCH FOUND (score={match['score']}) — source: \"{match['matched_source_text'][:60]}\" -> reply: \"{reply_text[:60]}\"")
                                log_jarvis_interaction(username, clean_prompt, "ECHO", reply_text)
                            else:
                                reply_text = None
                                print(f"Echo Chamber: NO MATCH FOUND for \"{clean_prompt[:60]}\" — reacting instead.")
                                log_jarvis_interaction(username, clean_prompt, "GHOSTED")
                                
                                try:
                                    no_reply_emojis = ["👀", "🤷", "🤔", "💀", "😶", "❓", "👍🏻", "👅"]
                                    chosen_emoji = random.choice(no_reply_emojis)
                                    scraper.cl.direct_send_reaction(thread_id, command_msg.id, chosen_emoji)
                                    print(f"Reacted with {chosen_emoji} to message.")
                                except Exception as e:
                                    print(f"Could not react to message: {e}")

                    if reply_text:
                        scraper.send_message(thread_id, reply_text, reply_to_message=command_msg)
                    print("💤 Resuming background watch loop...")

            # Reset error counter on successful cycle
            consecutive_errors = 0

        except Exception as e:
            consecutive_errors += 1
            print(f"\nPolling Warning: {e} - retrying in 5 seconds... ({consecutive_errors}/10)")

            if consecutive_errors >= 10:
                stop_time = datetime.now().strftime("%I:%M:%S %p on %d/%m/%Y")
                print("\n" + "🚨" * 20)
                print(" AUTO-KILL SWITCH ENGAGED ")
                print(" 10 consecutive API/Network errors encountered.")
                print(f" Bot safely stopped at: {stop_time}")
                print("🚨" * 20 + "\n")
                sys.exit(1)

            time.sleep(5)
            continue

        # Human-like randomized polling delay (4.0s - 7.5s)
        time.sleep(random.uniform(4.0, 7.5))

if __name__ == "__main__":
    main()