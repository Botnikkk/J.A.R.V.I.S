import random


def format_response_time(seconds):
    if seconds is None:
        return "no data"
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds/60:.1f} min"
    if seconds < 86400:
        return f"{seconds/3600:.1f} hr"
    return f"{seconds/86400:.1f} days"


def extract_user_ids_from_command(text, command_word, user_mapping, max_users=2):
    """Scans every word in the message for a known username (with or
    without a leading @), case-insensitive. Skips the 'jarvis' trigger
    word and the command word itself."""
    reverse = {v.lower(): k for k, v in user_mapping.items()}
    tokens = text.split()
    found = []
    skip_words = {"jarvis", command_word.lower()}
    for tok in tokens:
        clean = tok.lstrip('@').strip(",.!?").lower()
        if clean in skip_words:
            continue
        if clean in reverse and reverse[clean] not in found:
            found.append(reverse[clean])
        if len(found) >= max_users:
            break
    return found


def format_vs(name1, stats1, name2, stats2):
    lines = [f"⚔️ {name1} vs {name2} ⚔️\n"]
    lines.append(f"Messages sent: {name1} {stats1['message_count']} — {stats2['message_count']} {name2}")
    lines.append(f"Avg words/msg: {name1} {stats1['avg_words']:.1f} — {stats2['avg_words']:.1f} {name2}")
    lines.append(
        f"Avg response time: {name1} {format_response_time(stats1['avg_response_seconds'])} — "
        f"{format_response_time(stats2['avg_response_seconds'])} {name2}"
    )
    lines.append(f"One-word replies: {name1} {stats1['one_word_pct']:.0f}% — {stats2['one_word_pct']:.0f}% {name2}")

    score1 = stats1['message_count'] + stats1['avg_words']
    score2 = stats2['message_count'] + stats2['avg_words']
    if stats1['avg_response_seconds'] is not None:
        score1 += max(0, 600 - min(stats1['avg_response_seconds'], 600)) / 60
    if stats2['avg_response_seconds'] is not None:
        score2 += max(0, 600 - min(stats2['avg_response_seconds'], 600)) / 60

    if score1 > score2:
        lines.append(f"\n🏆 {name1} wins this round.")
    elif score2 > score1:
        lines.append(f"\n🏆 {name2} wins this round.")
    else:
        lines.append("\n🤝 Dead even. Suspiciously even.")

    return "\n".join(lines)


def format_random(username, msg):
    return f"{username} said :- {msg.text}"


# ---------------------------------------------------------------------------
# ROASTS — every category is driven by a real stat from get_user_stats().
# One matching category is picked at random, then one line within it, so
# repeat roasts on the same person stay fresh.
# ---------------------------------------------------------------------------

ROAST_TEMPLATES = {
    "one_word": [
        "Why use many word when one word do trick? {name} embraces the caveman lifestyle with {pct:.0f}% one-word replies across {count} messages.",
        "{name} has sent {count} messages and {pct:.0f}% of them are a single word. We get it, you're mysterious and emotionally unavailable.",
        "{name} types like they're being charged by the syllable. {pct:.0f}% of their {count} messages are exactly one word.",
        "Somewhere, a thesaurus is crying. {name} hit a staggering {pct:.0f}% one-word reply rate over {count} messages.",
        "{name} could communicate entirely in Morse code and lose absolutely zero nuance — {pct:.0f}% one-worders.",
        "{name} found the 'k' key and built an entire personality around it. {pct:.0f}% one-word messages.",
    ],

    "slow_responder": [
        "{name} takes an average of {resp} to reply. I've seen cheeses age faster.",
        "By the time {name} replies ({resp} average delay), we've all grown as people and moved on.",
        "With an average response time of {resp}, {name} is living proof that time travel to the future is possible—just wait for their text.",
        "{name}'s average response time is {resp}. Even Internet Explorer is embarrassed for you.",
        "{resp} average reply speed. Glaciers literally melt faster than {name} types.",
    ],

    "ghost": [
        "{name} averages {resp} before replying. At this point, just send a carrier pigeon, it'll get here faster.",
        "{name} has completely ghosted us with an average delay of {resp}. I was this close to calling your emergency contact.",
        "{resp} average response time. {name} isn't just slow, they're basically in witness protection.",
        "The group chat has shifted through five different eras by the time {name} finally replies — {resp} average.",
    ],

    "fast_responder": [
        "{name} replies in an average of {resp}. Blink twice if you're trapped inside the group chat server.",
        "{resp} average response time. {name}, it is okay to put the phone down. The chat will survive without you.",
        "{name} responds in {resp} flat. That's not socializing, that's a clinical reflex.",
        "Nobody replies in {resp} on average unless the notification sound is their actual heartbeat. Looking at you, {name}.",
    ],

    "caps": [
        "{name} is SHOUTING in {pct:.0f}% of their messages. Who hurt you, and why are you taking it out on our eardrums?",
        "{name} hasn't met a lowercase letter they liked in years — {pct:.0f}% all-caps energy.",
        "{pct:.0f}% of {name}'s messages are in caps. Take a deep breath. Lower your voice.",
        "Is {name} texting or reading a declaration of war? {pct:.0f}% caps lock usage heavily suggests the latter.",
    ],

    "low_effort": [
        "{name} averages a miserable {avg_words:.1f} words per message. Are you paying for data by the letter?",
        "{avg_words:.1f} words per message. {name} peaked in efficiency and absolutely bottomed out in effort.",
        "{name} communicates in what can generously be called 'grunts' — {avg_words:.1f} words per message.",
        "At {avg_words:.1f} words per message, {name} is texting in haiku, minus the art, thought, or talent.",
    ],

    "essay_writer": [
        "{name} averages {avg_words:.1f} words per message. Nobody is reading all that. Happy for you though, or sorry that happened.",
        "{avg_words:.1f} words per message. {name} really said 'let me drop a dissertation in the chat real quick'.",
        "{name} treats every reply like they're being graded on a rubric — {avg_words:.1f} words per message.",
        "Somebody get {name} a Substack. {avg_words:.1f} words per message is psychotic behavior for a casual group chat.",
    ],

    "wall_of_text": [
        "{name} hit us with a {chars}-character manifesto. Sir, this is a Wendy's.",
        "{chars} characters in a single message. {name} definitely typed this in the Notes app first while shaking with rage.",
        "Somewhere, {name}'s {chars}-character magnum opus sits entirely unread by everyone in this chat.",
    ],

    "high_volume": [
        "{name} has sent {count} messages. Your screen time report must look like a cry for help.",
        "{count} messages and counting from {name}. Unemployed behavior.",
        "{name} is single-handedly keeping the servers running with {count} messages. Go outside. Touch grass.",
        "At {count} messages, {name} has decided they are the main character of this group chat. We are just the audience.",
    ],

    "low_volume": [
        "{name} has sent a grand total of {count} messages. Do you charge an appearance fee, or are you just here to spy?",
        "{count} messages from {name}. Lurking at a professional, almost terrifying level.",
        "{name} shows up in this chat about as often as Halley's Comet — {count} messages total.",
        "{count} messages ever. {name} is basically a background NPC in our storyline.",
    ],

    "question_spammer": [
        "{pct:.0f}% of {name}'s messages end in a question mark. My sibling in Christ, we are not ChatGPT.",
        "{name} asks a question {pct:.0f}% of the time. I am begging you to learn how to use Google.",
        "{pct:.0f}% question rate. {name} treats this group chat like an underpaid IT support desk.",
    ],

    "exclaimer": [
        "{name} ends {pct:.0f}% of their messages with an exclamation mark. Exhausting golden retriever energy.",
        "{name} literally cannot send a text without yelling excitedly {pct:.0f}% of the time. Chill out!!",
        "{pct:.0f}% exclamation rate — {name} narrates their own mundane life like a desperate hype man.",
    ],

    "night_owl": [
        "{name} sends {pct:.0f}% of their messages between midnight and 5 AM. Melatonin is available over the counter, you know.",
        "{name} is only active in the dead of night — {pct:.0f}% of messages sent from 12am–5am. Absolute goblin behavior.",
        "{pct:.0f}% of {name}'s texts come from the witching hours. Honestly, I'm worried about your REM sleep.",
    ],

    "early_bird": [
        "{name} fires off messages before 9 AM {pct:.0f}% of the time. Tone down the morning person propaganda, it's sickening.",
        "{name} is out here texting at 6 AM like it's a normal thing to do. {pct:.0f}% of their messages are unhinged early.",
        "{pct:.0f}% early-morning texting rate. {name} has already lived a full day before the rest of us even find our slippers.",
    ],

    "weekend_warrior": [
        "{pct:.0f}% of {name}'s messages are sent on weekends. Corporate slave by day, chat menace by weekend.",
        "{name} completely disappears on weekdays. {pct:.0f}% of their texts prove they only exist from Friday to Sunday.",
        "{pct:.0f}% weekend activity. {name} clearly has a soul-crushing 9-to-5 keeping them violently silenced during the week.",
    ],

    "double_texter": [
        "{name} is just talking to themselves {pct:.0f}% of the time. Double-texting is a disease, and you are patient zero.",
        "{name} double (and triple) texts {pct:.0f}% of the time. The concept of patience is completely lost on this one.",
        "{pct:.0f}% of {name}'s messages follow their own previous message. A stunning, tragic one-man play.",
    ],

    "vocabulary_king": [
        "{name} has a vocabulary richness of {vocab:.0%}. Okay, we get it, you read a book once.",
        "{vocab:.0%} unique word usage from {name}. Someone swallowed a thesaurus for breakfast.",
        "{name}'s vocabulary diversity sits at {vocab:.0%}. The rest of us are out here saying 'lol' and 'vibes' on repeat.",
    ],

    "repetitive_vocab": [
        "{name}'s vocabulary diversity is at a pathetic {vocab:.0%}. I've seen better verbal processing from a smart fridge.",
        "{vocab:.0%} unique word usage. {name} operates entirely on a rotation of about five overused phrases.",
        "{name} recycles vocabulary at a {vocab:.0%} uniqueness rate. NPC dialogue tree confirmed.",
    ],

    "conversation_starter": [
        "{name} has performed CPR on this dead chat {starts} times. Let it rest in peace, buddy.",
        "{starts} times {name} has dragged this chat out of the grave. A true martyr to the cause.",
        "{name} single-handedly refused to let the vibes die {starts} times. Somebody pay them for their emotional labor.",
    ],

    "generic": [
        "{name} sent {count} messages and somehow managed to say absolutely nothing of substance.",
        "{name} contributed {count} messages to this chat. They were certainly words. Typed on a keyboard. Sent to us.",
        "{count} messages from {name}, and zero personality traits successfully transmitted.",
        "{name}'s stats ({count} messages) read like the ultimate participation trophy.",
        "Analyzed {count} messages from {name}. Conclusion: oxygen thief.",
    ],
}


def _build_candidates(stats):
    candidates = []

    if stats["one_word_pct"] >= 30:
        candidates.append(("one_word", {"pct": stats["one_word_pct"]}))

    if stats["avg_response_seconds"] is not None:
        if stats["avg_response_seconds"] >= 21600:  # 6+ hours
            candidates.append(("ghost", {"resp": format_response_time(stats["avg_response_seconds"])}))
        elif stats["avg_response_seconds"] >= 1800:  # 30+ min
            candidates.append(("slow_responder", {"resp": format_response_time(stats["avg_response_seconds"])}))
        elif stats["avg_response_seconds"] <= 5:
            candidates.append(("fast_responder", {"resp": format_response_time(stats["avg_response_seconds"])}))

    if stats["caps_pct"] >= 20:
        candidates.append(("caps", {"pct": stats["caps_pct"]}))

    if stats["avg_words"] <= 3:
        candidates.append(("low_effort", {"avg_words": stats["avg_words"]}))
    elif stats["avg_words"] >= 15:
        candidates.append(("essay_writer", {"avg_words": stats["avg_words"]}))

    if stats["longest_message_length"] >= 300:
        candidates.append(("wall_of_text", {"chars": stats["longest_message_length"]}))

    if stats["message_count"] >= 500:
        candidates.append(("high_volume", {}))
    elif stats["message_count"] <= 5:
        candidates.append(("low_volume", {}))

    if stats["question_pct"] >= 20:
        candidates.append(("question_spammer", {"pct": stats["question_pct"]}))

    if stats["exclaim_pct"] >= 40:
        candidates.append(("exclaimer", {"pct": stats["exclaim_pct"]}))

    if stats["night_owl_pct"] >= 25:
        candidates.append(("night_owl", {"pct": stats["night_owl_pct"]}))

    if stats["early_bird_pct"] >= 20:
        candidates.append(("early_bird", {"pct": stats["early_bird_pct"]}))

    if stats["weekend_pct"] >= 40:
        candidates.append(("weekend_warrior", {"pct": stats["weekend_pct"]}))

    if stats["double_text_pct"] >= 35:
        candidates.append(("double_texter", {"pct": stats["double_text_pct"]}))

    if stats["vocab_richness"] is not None:
        if stats["vocab_richness"] >= 0.6:
            candidates.append(("vocabulary_king", {"vocab": stats["vocab_richness"]}))
        elif stats["vocab_richness"] <= 0.3:
            candidates.append(("repetitive_vocab", {"vocab": stats["vocab_richness"]}))

    if stats["conversation_starts"] >= 5:
        candidates.append(("conversation_starter", {"starts": stats["conversation_starts"]}))

    return candidates


def format_roast(name, stats):
    candidates = _build_candidates(stats)

    if not candidates:
        category, extra = "generic", {}
    else:
        category, extra = random.choice(candidates)

    template = random.choice(ROAST_TEMPLATES[category])
    return template.format(name=name, count=stats["message_count"], **extra)
def format_convo(convo_messages, user_mapping):
    lines = ["🗣️ OUT OF CONTEXT CONVO 🗣️\n"]
    for msg in convo_messages:
        name = user_mapping.get(str(msg.user_id), "Someone")
        lines.append(f"@{name} said:\n\"{msg.text}\"\n")
    return "\n".join(lines).strip()

def format_qna(qna_messages, user_mapping):
    q_msg, a_msg = qna_messages
    q_name = user_mapping.get(str(q_msg.user_id), "Someone")
    a_name = user_mapping.get(str(a_msg.user_id), "Someone")
    
    return (f"❓ THE Q&A ❓\n\n"
            f"@{q_name} asked:\n\"{q_msg.text}\"\n\n"
            f"@{a_name} answered:\n\"{a_msg.text}\"")