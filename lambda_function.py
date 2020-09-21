import datetime
import requests
import boto3
import os
import json
import tweepy

twitter_api_key = os.environ['twitter_api_key']
twitter_api_secret = os.environ['twitter_api_secret']
twitter_access_token = os.environ['twitter_access_token']
twitter_access_token_secret = os.environ['twitter_access_token_secret']


def get_twitter_auth():
    try:
        auth = tweepy.OAuthHandler(twitter_api_key,
                                   twitter_api_secret)
        auth.set_access_token(twitter_access_token,
                              twitter_access_token_secret)
    except KeyError:
        print("Please check the environment variables for the twitter environment variables")
    except:
        print("An unexpected error occured")
    else:
        return auth


tweets = []


def lambda_handler(event, context):
    relevant_field_tweets = \
        twitter_search(event["twitter_search"])
    push_to_bucket(event["bucket_name"],
                   event["key"],
                   relevant_field_tweets)
    invalidate_cdn(event["cdn"], event["key"])
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


# Dhara wanted dates  in the form of August 01, 2017

def change_time_format(date_string):
    input_format = "%a %b %d %H:%M:%S %z %Y"
    output_format = "%B %d, %Y"
    date_object = datetime.datetime.strptime(date_string, input_format)
    return date_object.strftime(output_format)


def push_to_bucket(bucket_name, key, data_object):
    s3 = boto3.resource("s3")
    print("Publishing tweets to {}/{}".format(bucket_name, key))
    bucket = s3.Bucket(bucket_name)
    bucket.put_object(Key=key,
                      ACL='public-read',
                      Body=json.dumps(data_object),
                      ContentType="application/json")


def invalidate_cdn(kwargs, key):
    url = "https://d9y49oyask.execute-api.ap-south-1.amazonaws.com/production/cloudfront/invalidate"
    params = {}
    if kwargs["source"] == "CloudFront":
        params["source"] = kwargs["source"]
        params["quantity"] = 1
        params["distribution_id"] = kwargs["creds"]["distribution_id"]
        creds = {'aws_access_key_id': kwargs["creds"]["aws_access_key_id"],
                 'aws_secret_access_key': kwargs["creds"]["aws_secret_access_key"]}
        params["credentials"] = creds
        params["invalidation_items"] = ["/nl-silenced/twitter.json"]
    elif kwargs["source"] == "Akamai":
        params["source"] = kwargs["source"]
        creds = {}
        creds["host"] = kwargs["creds"]["host"]
        creds["client_secret"] = kwargs["creds"]["client_secret"]
        creds["client_token"] = kwargs["creds"]["client_token"]
        creds["access_token"] = kwargs["creds"]["access_token"]
        params["credentials"] = creds
        params["invalidation_items"] = \
            ['protograph.indianexpress.com/toReportViolence/twitter.json']

    requests.post(url,
                  json=params,
                  headers={"accept": "json",
                           "x-api-key": os.environ["aws_api_key"]})


def twitter_search(search_terms):
    auth = get_twitter_auth()

    # Initializes api with credentials for twitter
    api = tweepy.API(auth)
    search_terms = search_terms.split(',')
    for i in range(len(search_terms)):
        search_terms[i] = search_terms[i].strip()

    # Twitter api keyword
    # Use https://dev.twitter.com/rest/public/search
    # for more complex search queries

    search_string = " ".join(search_terms)
    a = api.search(q=search_string, geocode="22.199166,78.476681,1200mi")
    # tweepy status object has a _json hash
    # that can be used to convert to json
    tweets = json.dumps([status._json for status in a])
    tweets = json.loads(tweets)
    relevant_field_tweets = []
    for tweet in tweets:
        relevant_field_tweet = get_relevant_fields(tweet)
        # # Twitter adds a retweeted_status field if a
        # # tweet is a retweet. We require only original tweets
        # if "retweeted_status" not in tweet:
        relevant_field_tweets.append(relevant_field_tweet)

    return relevant_field_tweets
