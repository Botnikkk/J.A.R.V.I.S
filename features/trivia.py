class TriviaManager:
    def __init__(self):
        self.active_trivia = None

        self.aliases = {
            "_niiikkk._": ["nikkk", "nik", "nikk", "nikki",  "nikhil"],
            "vishhwashh": ["vishwash", "vish",  "vishu"],
            "hiiibaahhhhhh": ["hibi", "hiba"],
            "dhee_znuts": ["dheeraj", "dihraj"],
            "harharmahadev4lhareram": ["dazai", "sanket"],
            "rya_.xd": ["arya", "rya"],
            "xr1q0": ["miya", "mimi"],
            "onlyfaisals": [ "faisal", "fesu", "fesl"],
            "mub1h_": [ "mubih", "mubi"],
            "beatopi4a": ["safwa", "safu"],
            "rizashaiikhh": ["riza", "du dah"],
            "shreyas2icy": ["shreyas"],
            "fl3xture": ["deba", "debayudh"],
            "zuzuuulover": ["arya", "rya"],
            "hellotoffnuffin": ["ritin", "ritu"],
            "_.sora._.______": ["sora"],
            "tanye.westtttt": ["tanya"],
            "notyour_nish_": ["nish", "nishtha"],
        }

    def start_game(self, quote_data, user_mapping):
        author_id = str(quote_data["author_id"])
        author_name = user_mapping.get(author_id, "Unknown")

        self.active_trivia = {
            "author_id": author_id,
            "author_name": author_name,
            "hint": quote_data.get("date_hint", "the past")
        }

        return f"🕵️‍♂️ **WHO SAID IT?** 🕵️‍♂️\n\n\"{quote_data['text']}\"\n\nGuess who said this! First correct name or nickname wins."

    def get_answer(self):
        if not self.active_trivia:
            return "⚠️ There is no active trivia game right now! Type 'jarvis whosaidit' to start one."

        ans_name = self.active_trivia['author_name']
        self.active_trivia = None
        return f"🚨 THE ANSWER IS... 🚨\n\nIt was @{ans_name}"

    def check_guess(self, text):
        """Returns True if the text contains the username or an alias."""
        if not self.active_trivia or not text:
            return False

        target_username = self.active_trivia['author_name']

        clean_text = ''.join(c if c.isalnum() else ' ' for c in text.lower())
        tokens = set(clean_text.split())

        valid_answers = {target_username.lower()}

        if target_username in self.aliases:
            for alias in self.aliases[target_username]:
                valid_answers.add(alias.lower())

        for ans in valid_answers:
            if ans in tokens:
                return True

        return False
