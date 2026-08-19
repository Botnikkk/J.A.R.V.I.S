import re
import random

def _normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

SMALLTALK = [
    {
        "patterns": {"hi", "hey", "hello", "hy", "heyy", "heyyy", "yo", "sup", "wassup", "whats up", "hlo", "hloo", "aur"},
        "responses": [
            "yo", 
            "sup", 
            "hey hey", 
            "wassup",
            "bol nalle", 
            "kya hai bhai?", 
            "bol", 
            "bhaunk",
            "sup g",
            "bol bhadvu"
        ],
    },
    {
        "patterns": {"by", "bye", "cya", "gtg", "goodbye", "bye bye", "brb"},
        "responses": [
            "bye", 
            "cya", 
            "later",
            "nikal", 
            "jaa na bhai kon rok raha", 
            "finally shanti", 
            "dafa ho lun ke",
            "cya nerd",
            "nikal bhadvu"
        ],
    },
    {
        "patterns": {"goodmorning", "good morning", "gm", "morning"},
        "responses": [
            "morning", 
            "gm", 
            "uth gaya bhalu?", 
            "so hi jata hamesha ke liye",
            "jaago jaago subah hogyi",
            "uth gaya lun ke?"
        ],
    },
    {
        "patterns": {"goodnight", "good night", "gn", "night", "nighty"},
        "responses": [
            "night", 
            "gn", 
            "sleep well",
            "soja chup chap", 
            "bhagwan ke liye soja", 
            "gn nalle", 
            "dekhte hai kitni der me wapas aayega chat me",
            "soja bhadvu",
        ],
    },
    {
        "patterns": {"i love you", "love you", "ily"},
        "responses": [
            "love you too ig", 
            "noted", 
            "🫡",
            "padhai karle", 
            "chhi bhai",
        ],
    },
    {
        "patterns": {"how are you", "how you doing", "hows it going", "hru", "kese ho", "kse ho", "kya haal"},
        "responses": [
            "surviving on group chat energy",
            "living the dream, one poll cycle at a time",
            "can't complain, no one's roasted me yet",
            "zinda hu bas", 
            "tere se toh acha hu", 
            "surviving on this gc's toxic energy"
        ],
    },
    {
        "patterns": {"are you real", "are you alive", "are you sentient", "are you human", "do you have feelings"},
        "responses": [
            "real enough to remember every message you've ever sent",
            "define real",
            "i'm as real as your sleep schedule",
            "tere dimaag se jyada real hu", 
            "code hu bhai, tera baap nahi", 
            "ha bhai tere phone ke andar baitha hu"
        ],
    },
    {
        "patterns": {"thanks", "thank you", "ty", "tysm", "thx"},
        "responses": [
            "np", 
            "anytime", 
            "🫡",
            "ehsaan mat bhoolna", 
            "paise nikal pehle", 
            "ha thik hai ab rula mat",
            "np bhadvu"
        ],
    },
    {
        "patterns": {"you suck", "you suck fr", "youre useless", "you're useless", "you suck bro", "chutiya", "chutiye"},
        "responses": [
            "skill issue on your end tbh",
            "and yet you keep typing to me",
            "harsh, considering i remember everything you've ever said here",
            "apna thobda dekh pehle", 
            "tu konsa shehensha hai", 
            "cry about it",
            "thopda dekh apna lun ke",
            "shut up bhadvu"
        ],
    },
    {
        "patterns": {"im bored", "bored", "bore ho raha", "kuch karo"},
        "responses": [
            "toh main kya nachu?", 
            "kuch kaam dhandha karle nalle", 
            "padhai karle bhai",
            "go touch some grass",
        ],
    },
    {
        "patterns": {"wyd", "kya kar raha", "what are you doing", "what r u doing"},
        "responses": [
            "teri tarah vella nahi hu", 
            "judging you heavily", 
            "group chat ki bakchodi padh raha hu",
            "chilling. tu apna bata",
            "logging your messages"
        ],
    },
    {
        "patterns": {"who made you", "tera baap kon hai", "who is your boss", "who created you","who is nikkk", "what is nikkk", "nikkk"},
        "responses": [
            "tera baap", 
            "my creator",
            "deddy ji"
        ],
    }
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