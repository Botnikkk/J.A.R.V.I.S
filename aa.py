from instagrapi import Client

cl = Client()
# Log in using the session ID that you know works on the laptop
cl.login_by_sessionid("37797976551%3AetNX9OibczGzSs%3A14%3AAYhN_3R8f_6AYXssIkdfwbzx5Uda9DH2kwD7e9cOhQ")

# Dump the entire trusted device footprint into a file
cl.dump_settings("settings.json")
print("Settings saved successfully!")