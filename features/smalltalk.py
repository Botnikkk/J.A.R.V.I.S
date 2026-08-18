import re
import random

def _normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

SMALLTALK = [
    {
        "patterns": {"hi", "hey", "hello", "hy", "heyy", "heyyy", "yo", "sup", "wassup", "whats up","hlo","hloo"},
        "responses": ["yo", "sup", "hey hey", "wassup"],
    },
    {
        "patterns": {"by","bye", "cya", "gtg", "goodbye", "bye bye"},
        "responses": ["bye", "cya", "later"],
    },
    {
        "patterns": {"goodmorning", "good morning", "gm", "morning"},
        "responses": ["morning", "gm", "wake up on the right side today?"],
    },
    {
        "patterns": {"goodnight", "good night", "gn", "night", "nighty"},
        "responses": ["night", "gn", "sleep well"],
    },
    {
        "patterns": {"i love you", "love you", "ily"},
        "responses": ["love you too ig", "noted", "🫡"],
    },
    {
        "patterns": {"how are you", "how you doing", "hows it going", "hru"},
        "responses": [
            "surviving on group chat energy",
            "living the dream, one poll cycle at a time",
            "can't complain, no one's roasted me yet",
        ],
    },
    {
        "patterns": {"are you real", "are you alive", "are you sentient", "are you human", "do you have feelings"},
        "responses": [
            "real enough to remember every message you've ever sent",
            "define real",
            "i'm as real as your sleep schedule",
        ],
    },
    {
        "patterns": {"thanks", "thank you", "ty", "tysm"},
        "responses": ["np", "anytime", "🫡"],
    },
    {
        "patterns": {"you suck", "you suck fr", "youre useless", "you're useless", "you suck bro"},
        "responses": [
            "skill issue on your end tbh",
            "and yet you keep typing to me",
            "harsh, considering i remember everything you've ever said here",
        ],
    },
]

def get_smalltalk_reply(text):
    """Returns a canned reply if the message (normalized) exactly matches a
    known smalltalk pattern, else None. Exact match, not substring, so
    'hy' won't false-positive inside an unrelated longer message."""
    normalized = _normalize(text)
    for entry in SMALLTALK:
        if normalized in entry["patterns"]:
            return random.choice(entry["responses"])
    return None