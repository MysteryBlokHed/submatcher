# Created by MysteryBlokHed in 2019.
import json
import praw
import threading
from time import sleep

USERNAME = "submatcher"
SUB = "submatcher"
SIGNUP_POST_ID = "dg4qt2"
RUN_PER_X_MINUTES = 60

SUB_MATCH_THRESHOLD = 5
FAVOURITE_SUB_MATCH_THRESHOLD = 2

reddit = praw.Reddit(USERNAME)
signup_post = reddit.submission(id=SIGNUP_POST_ID)

class SignupThread(threading.Thread):
    def run(self):
        # Open users subs db
        f = open("users_subs.json", "r")
        users_subs = json.loads(f.read())
        f.close()

        ### Check for new sign ups
        for message in reddit.inbox.stream():
            if message.subreddit == SUB: # Check if the sub is correct
                if message.parent() == signup_post: # Check if the comment is on the signup post
                    user = message.author.name
                    if user not in users_subs: # Make sure that the user has not signed up yet
                        users_subs[message.author.name] = {"all": [], "favourites": []}
                        mode = 0
                        for line in message.body.split("\n"):
                            if line == "[ALL]":
                                mode = 1
                            elif line == "[FAVOURITES]":
                                mode = 2
                            
                            # Add subs to database
                            if mode == 1:
                                if line != "[ALL]" and line.lower() not in users_subs[user]["all"]: users_subs[user]["all"].append(line.lower())
                            elif mode == 2:
                                if line.lower() in users_subs[user]["all"] and line.lower() not in users_subs[user]["favourites"]: users_subs[user]["favourites"].append(line.lower())
                        
                        # Write changes to file
                        f = open("users_subs.json", "w")
                        f.write(json.dumps(users_subs))
                        f.close()

                        message.reply(f"Successfully signed up!  \nAll subs list: {str(users_subs[user]['all']).strip('[').strip(']')}\n\nFavourite subs list: {str(users_subs[user]['favourites']).strip('[').strip(']')}").upvote()
                        print(f"Created account for u/{user}.")
                        message.mark_read()
                        message.mod.remove()
                    else:
                        # Add subs to account
                        newly_added = []
                        fav_added = []

                        mode = 0
                        for line in message.body.split("\n"):
                            if line == "[ADD]":
                                mode = 1
                            elif line == "[FAVOURITES_ADD]":
                                mode = 2
                            
                            # Add subs to database
                            if mode == 1:
                                if line != "[ADD]" and line.lower() not in users_subs[user]["all"]:
                                    users_subs[user]["all"].append(line.lower())
                                    newly_added.append(line)
                            elif mode == 2:
                                if line.lower() in users_subs[user]["all"] and line.lower() not in users_subs[user]["favourites"]:
                                    users_subs[user]["favourites"].append(line.lower())
                                    fav_added.append(line)
                        
                        # Write changes to file
                        f = open("users_subs.json", "w")
                        f.write(json.dumps(users_subs))
                        f.close()

                        message.reply(f"Subs added: {str(newly_added).strip('[').strip(']')}\n\nFavourite subs added: {str(fav_added).strip('[').strip(']')}")
                        print(f"Added subs to u/{user}'s account.")
                        message.mark_read()
                        message.mod.remove()

                        # message.reply(f"You have already signed up!  \nFor instructions on how to add subs to your account, go [here]({INSTRUCTIONS_POST_URL}).").upvote()
                        # print(f"Didn't create account for u/{user} as they already have one.")
                        # message.mark_read()

class MatchThread(threading.Thread):
    def run(self):
        # Open users subs db
        f = open("users_subs.json", "r")
        users_subs = json.loads(f.read())
        f.close()

        # Read matches file
        f = open("matches.json")
        matches = json.loads(f.read())
        f.close()
        
        # Loop
        while True:
            ### Try to match users
            for user_a in users_subs:
                for user_b in users_subs:
                    if user_a != user_b and user_a+"|||||"+user_b not in matches and user_b+"|||||"+user_a not in matches: # Make sure it's not the exact same user and that the users haven't matched yet
                        all_subs_match = []
                        favourite_subs_match = []

                        # Check in all sub lists for ones that match
                        for sub in users_subs[user_a]["all"]:
                            if sub in users_subs[user_b]["all"]:
                                all_subs_match.append(sub)
                        for sub in users_subs[user_a]["favourites"]:
                            if sub in users_subs[user_b]["favourites"]:
                                favourite_subs_match.append(sub)
                        
                        print(all_subs_match)
                        print(favourite_subs_match)

                        # Check if it was a match
                        if len(all_subs_match) >= SUB_MATCH_THRESHOLD or len(favourite_subs_match) >= FAVOURITE_SUB_MATCH_THRESHOLD:
                            # Notify both parties
                            try:
                                # Find all subs in common
                                subs_match = favourite_subs_match
                                for sub in all_subs_match:
                                    if sub not in subs_match:
                                        subs_match.append(sub)

                                reddit.redditor(user_a).message("Match!", f"You have matched with u/{user_b}! They have been notified as well.  \nCommon subs: {str(subs_match).strip('[').strip(']')}")
                                reddit.redditor(user_b).message("Match!", f"You have matched with u/{user_a}! They have been notified as well.  \nCommon subs: {str(subs_match).strip('[').strip(']')}")
                                print(f"u/{user_a} and u/{user_b} have matched.")
                                matches.append(user_a+"|||||"+user_b)

                                # Write changes to file
                                f = open("matches.json", "w")
                                f.write(json.dumps(matches))
                                f.close()
                            except Exception as e:
                                print(e)

            # Wait the set delay
            sleep(RUN_PER_X_MINUTES*60)

SignupThread().start()
MatchThread().start()