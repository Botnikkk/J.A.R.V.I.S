from instagrapi import Client

# Paste a fresh session ID here (same way you got IG_SESSION_ID originally —
# from your logged-in Instagram account's cookies in browser/app).
SESSION_ID = "34612692420%3AZDD79CJHZchco7%3A17%3AAYjKF3uqVyKhl38gZMk9Y8TiRLYqm5Qqce1i_d93bA"

cl = Client()
cl.login_by_sessionid(SESSION_ID)
cl.dump_settings("settings.json")

print(f"✅ New settings.json saved. Logged in as user_id: {cl.user_id}")