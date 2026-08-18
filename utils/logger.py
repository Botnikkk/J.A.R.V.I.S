import os
from datetime import datetime

def log_jarvis_interaction(username, prompt, outcome, reply_text=None):
    """
    Auto-generates jarvis_interactions.txt if it doesn't exist, 
    and logs what was said, how JARVIS handled it, and what he replied.
    Outcomes: [COMMAND], [SMALLTALK], [ECHO], [GHOSTED]
    """
    file_path = "jarvis_interactions.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    # If the file doesn't exist, create it automatically with a clean header
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=== JARVIS INTERACTION & SHADOW LOG ===\n\n")

    # Format the log entry based on whether he replied or ghosted
    if reply_text:
        log_line = f"[{timestamp}] [{outcome}] {username}: \"{prompt}\" ➔ JARVIS replied: \"{reply_text}\"\n"
    else:
        log_line = f"[{timestamp}] [{outcome}] {username}: \"{prompt}\" ➔ GHOSTED (No valid match)\n"
    
    # Append to the log file safely
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(log_line)