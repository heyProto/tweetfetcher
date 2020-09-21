import os
import pprint
import json
import sqlite3

import tweepy
from credentials import credentials

auth = tweepy.OAuthHandler(credentials['twitter_api_key'],
                           credentials['twitter_api_secret'])
auth.set_access_token(credentials['twitter_access_token'],
                      credentials['twitter_access_token_secret'])

# Initializes api with credentials for twitter
api = tweepy.API(auth)

directory = "tweet-data"

if not os.path.exists(directory):
    os.makedirs(directory)

conn = sqlite3.connect("tweet-data/tweet-data.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS tweets
(tweet text,
 hashtags text,
 author text,
 id_str text,
 status integer);''')

search_terms = input("Enter Hashtags separated by a comma:\n")
search_terms = search_terms.split(',')
for i in range(len(search_terms)):
    search_terms[i] = search_terms[i].strip()

# Twitter api keyword
# Use https://dev.twitter.com/rest/public/search
# for more complex search queries

search_string = " OR ".join(search_terms)
print(search_string)
a = api.search(q=search_string)
tweets = json.dumps([status._json for status in a])
tweets = json.loads(tweets)
tweets_array = []
for tweet in tweets:
    c.execute("SELECT * from tweets WHERE id_str=?", (tweet["id_str"],))
    existing_tweet = c.fetchall()
    if not existing_tweet == []:
        continue
    # Creates array of all information needed
    hashtags = []
    for each in tweet["entities"]["hashtags"]:
        hashtags.append(each["text"])

    tweets_array.append((tweet["text"],
                         ", ".join(hashtags),
                         tweet["user"]["name"],
                         tweet["id_str"],
                         0))

# print(pprint.PrettyPrinter().pprint(tweets_array))

c.executemany('INSERT INTO tweets VALUES (?,?,?,?,?);', tweets_array)
conn.commit()
conn.close()
