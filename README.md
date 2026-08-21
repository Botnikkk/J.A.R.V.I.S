# J.A.R.V.I.S - Instagram GC Bot

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/) [![Status](https://img.shields.io/badge/Status-Active-success?style=flat)](https://github.com/Botnikkk/J.A.R.V.I.S) 

This repository contains the source code for **J.A.R.V.I.S**, an autonomous, memory-driven Instagram Group Chat companion. Built in Python using `instagrapi`, it combines local chat analytics, interactive mini-games, dynamic roasts, and a self-improving echo chamber conversational engine—all while simulating human behavior to evade strict API detection.

**Bot ID :** [ J.A.R.V.I.S 🔗](https://www.instagram.com/jarvis.watcher)

---

## 🌟 Overview

J.A.R.V.I.S was created to turn a regular group chat into an interactive, entertaining space without triggering Instagram's aggressive anti-bot triggers. Instead of querying remote servers constantly, J.A.R.V.I.S maintains an active, growing **Local Message Store** cached directly from the chat. 

This localized database powers the bot's core systems:
* **Conversational AI (Echo Chamber & Smalltalk):** When mentioned, J.A.R.V.I.S scans its logged message database for contextual matches, mirroring the vernacular, inside jokes, and past responses of the group members like a tiny, organic machine learning model.
* **Interactive Chat Games & Commands:** Runs trivia guessing games ("Who Said It?"), pulls out-of-context quotes (`random`), stitches together past messages into fictional chats (`convo`) and interviews (`qna`), and calculates live group metrics.
* **Stat-Based Roasting & Comparisons:** Parses message volume and read-receipt response delays to deliver personalized, data-backed roasts and side-by-side head-to-head comparisons (`vs`).
* **Humanized Evasion Engine:** Maintains a circadian sleep rhythm at night, adjusts polling speeds adaptively based on chat activity, and gets distracted by scrolling meme pages to blend in with real human users.

---

## ✨ Key Features

### 💬 Conversational Intelligence
* **Echo Chamber Retrieval:** Searches historical conversation banks to find contextually relevant past replies from real members, allowing the bot to organically "speak" like the group.
* **Smalltalk Engine:** Evaluates common conversational remarks and greetings to reply instantly without sounding robotic.
* **Fallback Reactions:** If no fitting contextual reply exists in memory, J.A.R.V.I.S reacts naturally to the trigger message using randomized expressive emojis.

### 🎮 Fun, Trivia & Games
* **"Who Said It?" Trivia:** Pulls a random historical message from the database and challenges the group to guess who originally sent it, validating answers in real-time via user IDs.
* **Stat-Driven Roasts (`roast @user`):** Analyzes a member's messaging patterns, activity time zones, and ghosting habits to generate a personalized, statistical burn.
* **Head-to-Head Battles (`vs @user1 @user2`):** Compares two group members side-by-side across activity, total messages sent, and ignored rates.
* **Random Quote Retrieval (`random`):** Surfaces unexpected, out-of-context gems from past message logs.
* **Artificial Dialogues (`convo` & `qna`):** Synthesizes disconnected messages into hilarious multi-turn conversations and fictional Q&A interviews.

### 📊 Group Chat Analytics
* **Most Active / Top Talkers:** Ranks the most vocal contributors in the group chat.
* **Most Ignored Tracker:** Identifies who gets left on read most frequently based on calculated message response timeout windows.
* **File Exporter:** Structures logged messages into clean, user-specific text logs for local backups and data analysis.

### 🛡️ Stealth & Anti-Ban Architecture
* **Circadian Sleep Cycle:** Automatically enters a deep sleep mode during early morning hours (4:00 AM – 9:00 AM) to match authentic human sleeping schedules.
* **Adaptive Polling:** Automatically scales down polling intervals to 4–7 seconds when the chat is buzzing, and throttles back to 45–60 seconds when idle to conserve requests.
* **Meme Doomscrolling:** Randomly pauses between polling loops to fetch and explore cached meme pages, with a chance to forward funny reels back into the group chat or DMs.
* **Self-Healing Sessions:** Automatically validates session cookies, clears stale credentials on auth errors, and regenerates safe device footprints without manual intervention.

---

## 🛠️ Tech Stack & Architecture

* **Language:** **Python 3**
* **Core API:** Uses `instagrapi` for private mobile API handling.
* **Storage Layer:** Flat-file message logging paired with structured JSON session/device state caching.
* **Analysis Engine:** Custom text-tokenization, context heuristics, and statistical metrics parsing.
* **Deployment Target:** Designed for continuous background operation on Linux environments (including Ubuntu PRoot on Android Termux).

---

## 🤔 Why I Made This ?

The project began with a simple challenge during a late-night group chat when a friend asked: 
> "Could you build a bot to track our chat statistics, like who talks the most, or who gets left on read?"

I hadn't seen a **private, API-driven bot** deployed inside an Instagram group chat before, which immediately sparked my curiosity. After some research, I discovered a library called **`instagrapi`** and got to work. My initial prototype relied on a brute-force approach, attempting to pull massive chunks of chat history with every poll. Unsurprisingly, this was slow, inefficient, and quickly triggered Instagram's rate limits.

To resolve this, I optimized the architecture by implementing a **local message store**. The bot began quietly logging chat history into a local database, fetching only 5 to 10 new messages per request. Once this efficient data pipeline was in place, the project really gained momentum. 

I started by adding interactive mini-games, like a **"Who Said It?" trivia feature** that pulled random past quotes for the group to guess. I then expanded its capabilities to include commands for casual conversation, Q&As, and even a feature that playfully "roasted" group members using their actual chat data.

This led to a much bigger idea: what if the bot,  **J.A.R.V.I.S.**, could actually converse using that same database? 

I developed an **"Echo Chamber" mechanic**. When prompted, J.A.R.V.I.S. searches the database for contextually relevant replies previously sent by real group members. It effectively functions as a small, **organic machine learning model**; as our chat history expands, the bot's vocabulary, humor, and understanding of inside jokes evolve right alongside it.

To navigate Instagram's strict bot-detection algorithms, I programmed J.A.R.V.I.S. with **simulated human behaviors**, such as circadian sleep schedules and periodic meme-scrolling. While the project remains a work in progress and managing platform restrictions is an ongoing challenge, every new logged message helps J.A.R.V.I.S. feel less like a script and more like a genuine member of the group.