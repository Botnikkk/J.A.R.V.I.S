import re

class TriviaManager:
    def __init__(self):
        self.active_trivia = None

        # STRICTLY USER IDs AS KEYS. 
        # The FIRST item in the list is the default answer JARVIS will use if nobody guesses it.
        self.aliases = {
            "58236872636": ["nikkk", "nik", "nikk", "nikki",  "nikhil"],
            "58396043097": ["vishwash", "vish",  "vishu"],
            "48785894981": ["hibi", "hiba"],
            "46190340370": ["dheeraj", "dihraj"],
            "76984440251": ["dazai", "sanket"],
            "72220240749 ": ["dazai", "sanket"],
            "48269814265": ["arya", "rya"],
            "51602983262": ["arya", "rya"],
            "63988110496": ["miya", "mimi"],
            "22625167653": [ "faisal", "fesu", "fesl"],
            "8143648482": [ "mubih", "mubi"],
            "48043757344": ["safwa", "safu"],
            "9243900649": ["riza", "du dah"],
            "54994111283": ["shreyas"],
            "55553138760": ["deba", "debayudh"],
            "50710625258": ["ritin", "ritu"],
            "47762721374": ["sora"],
            "56233017544": ["tanya"],
            "56838775794": [ "nishtha", "nish"],
        }

    def start_game(self, analyzer, user_mapping, max_attempts=25):
        alert_printed = False

        for _ in range(max_attempts):
            quote_data = analyzer.get_whosaidit_quote(min_words=5)
            if not quote_data:
                break

            author_id = str(quote_data.get("author_id", ""))

            # Ensure the author is in our offline alias database
            if author_id not in self.user_aliases:
                if not alert_printed:
                    raw_name = user_mapping.get(author_id, f"Unknown_{author_id}")
                    print(f"\n🚨 [TRIVIA NOTICE] Encountered unlisted user (ID: {author_id} | @{raw_name}). Retrying with another quote...")
                    alert_printed = True
                continue

            self.active_trivia = {
                "author_id": author_id,
                "hint": quote_data.get("date_hint", "the past")
            }

            return f"🕵️‍♂️ **WHO SAID IT?** 🕵️‍♂️\n\n\"{quote_data['text']}\"\n\nGuess who said this! First correct name or nickname wins."

        return "⚠️ Couldn't find a quote from a registered member in the database. Try again."

    def get_answer(self):
        if not self.active_trivia:
            return "⚠️ There is no active trivia game right now! Type 'jarvis whosaidit' to start one."

        # Grabs the very first name in their alias list to reveal
        ans_name = self.user_aliases[self.active_trivia["author_id"]][0]
        self.active_trivia = None
        return f"🚨 THE ANSWER IS... 🚨\n\nIt was {ans_name}"

    def check_guess(self, text):
        """
        Returns the specific alias that was guessed correctly, or False if wrong.
        """
        if not self.active_trivia or not text:
            return False

        author_id = self.active_trivia["author_id"]
        valid_answers = self.user_aliases[author_id]

        clean_text = "".join(c if c.isalnum() else " " for c in text.lower())
        tokens = set(clean_text.split())

        for ans in valid_answers:
            ans_lower = ans.lower()
            # If they guessed this specific alias, return the alias itself!
            if ans_lower in tokens or ans_lower in clean_text:
                return ans

        return False