import requests
import json
import tweepy
from credentials import credentials
import datetime

auth = tweepy.OAuthHandler(credentials['twitter_api_key'],
                           credentials['twitter_api_secret'])
auth.set_access_token(credentials['twitter_access_token'],
                      credentials['twitter_access_token_secret'])
# Initializes api with credentials for twitter
api = tweepy.API(auth)

twitter_search = "#Lynchistan"

tweets = []
i = 0


def main():
    # Input from environment variables
    search_terms = twitter_search
    search_terms = search_terms.split(',')
    for i in range(len(search_terms)):
        search_terms[i] = search_terms[i].strip()

    # Twitter api keyword
    # Use https://dev.twitter.com/rest/public/search
    # for more complex search queries

    search_string = " OR ".join(search_terms)
    # http://tweepy.readthedocs.io/en/v3.5.0/api.html#API.search
    a = api.search(q=search_string, rpp=100)
    # tweepy status object has a _json hash
    # that can be used to convert to json
    tweets = json.dumps([status._json for status in a])
    tweets = json.loads(tweets)
    print("{} tweets found\n\n".format(len(tweets)))
    write_file("tweets-{}.json".format(search_string), tweets)
    relevant_field_tweets = []
    for tweet in tweets:
        print("Adding tweet === " + str(tweet["id"]) + ", " + str(i))
        relevant_field_tweet = get_relevant_fields(tweet)
        relevant_field_tweets.append(relevant_field_tweet)
        print("Added Tweet === " + str(tweet["id"]) + "\n\n")
        i += 1

    write_file("relevant-tweet-fields-{}.json".
               format(search_string), relevant_field_tweets)
    return relevant_field_tweets


def get_relevant_fields(tweet):
    flat_hash = {}
    flat_hash["title"] = tweet["user"]["name"] + " on Twitter"
    flat_hash["author"] = tweet["user"]["name"]
    flat_hash["author_url"] = "https://twitter.com/{}". \
                              format(tweet["user"]["screen_name"])
    flat_hash["site"] = "Twitter"
    flat_hash["canonical"] = "https://twitter.com/statuses/{}". \
                             format(tweet["id_str"])
    flat_hash["description"] = tweet["text"]
    flat_hash["date"] = change_time_format(tweet["created_at"])
    flat_hash["retweet_count"] = tweet["retweet_count"]
    flat_hash["favourites_count"] = tweet["favorite_count"]
    flat_hash["author_image"] = tweet["user"]["profile_image_url"]
    flat_hash["twitter_handle"] = tweet["user"]["screen_name"]
    url = None
    if tweet.get("entities", {}).get("media"):
        url = tweet["entities"]["media"][0]["media_url"]
        print("has-media")
    elif tweet.get("entities", {}).get("urls"):
        url = get_link_thumbnail(tweet["entities"]["urls"][0]["url"])
        print("has-url")
    if url:
        flat_hash["thumbnail_url"] = url

    return flat_hash


def get_link_thumbnail(link):
    params = {"url": link}
    r = requests.get("http://13.126.206.16:8000/iframely", params=params)
    data = json.loads(r.text)
    if data.get("links", {}).get("thumbnail"):
        return data["links"]["thumbnail"][0]["href"]
    else:
        return None


def write_file(file_name, data_object):
    with open("tweet-data/{}".format(file_name), "w") as f:
        f.write(json.dumps(data_object,
                           sort_keys=True,
                           indent=4,
                           separators=(',', ': ')))


def change_time_format(date_string):
    input_format = "%a %b %d %H:%M:%S %z %Y"
    output_format = "%B %d, %Y"
    date_object = datetime.datetime.strptime(date_string, input_format)
    return date_object.strftime(output_format)


print(main())
