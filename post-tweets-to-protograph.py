import json
import requests
import sqlite3
import re


# Regex removes utf8 characters above 3 bytes.
# MySql does not allow these characters
# https://github.com/openimages/dataset/issues/4
# For the regex re.compile(u'[\U00010000-\U0010ffff]')
# https://stackoverflow.com/a/10799465/5671433

def removeEmoji(text):
    # Replaces all unicode characters above 3 bytes
    # https://stackoverflow.com/a/26568779/5671433
    try:
        # Wide UCS-4 build
        emoji_pattern = re.compile(u'['
                                   u'\U0001F300-\U0001F64F'
                                   u'\U0001F680-\U0001F6FF'
                                   u"\U00010000-\U0010ffff"
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   u'\u2600-\u26FF\u2700-\u27BF]+',
                                   re.UNICODE)
    except re.error:
        # Narrow UCS-2 build
        emoji_pattern = re.compile(u'('
                                   u'\ud83c[\udf00-\udfff]|'
                                   u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
                                   u'[\u2600-\u26FF\u2700-\u27BF])+',
                                   re.UNICODE)

        return emoji_pattern.sub(r'', text)  # no emoji


conn = sqlite3.connect("tweet-data/tweet-data.db")
c = conn.cursor()
successful = []
for row in c.execute("SELECT * FROM tweets WHERE status=0"):
    tweet_url = "https://twitter.com/statuses/" + str(row[3])
    print(tweet_url)
    a = requests.get(
        "https://protograph-staging.pykih.com/api/v1/iframely",
        params={"url": tweet_url}
    )

    iframely = json.loads(a.text)

    # data attribute of payload
    data_attrs = {}
    data_attrs["title"] = iframely["title"]
    data_attrs["author"] = iframely["author"]
    data_attrs["author_url"] = iframely["author_url"]
    data_attrs["provider_name"] = iframely["site"]
    if "date" in iframely:
        data_attrs["date"] = iframely["date"]
    data_attrs["canonical"] = iframely["canonical"]
    data_attrs["description"] = row[0]
    data_attrs["url"] = tweet_url
    if "thumbnail_url" in iframely:
        data_attrs["thumbnail_url"] = iframely["thumbnail_url"]
    if "thumbnail_width" in iframely:
        data_attrs["thumbnail_width"] = iframely["thumbnail_width"]
    if "thumbnail_height" in iframely:
        data_attrs["thumbail_height"] = iframely["thumbanil_height"]

    # view_cast attribute of payload
    view_cast_attrs = {
        "account_id": 1,
        "template_datum_id": 6,
        "name": iframely["title"],
        "template_card_id": 6,
        "seo_blockquote": "<BLOCKQUOTE><H3>Title</H3><P>{}</P></BLOCKQUOTE>".
        format(removeEmoji(iframely["description"])),
        "optionalConfigJSON": "{}",
    }

    # source attribute of payload
    source_attrs = "twitter"

    # Hash to post to protograph
    payload = {}
    payload["datacast"] = {}
    payload["datacast"]["data"] = data_attrs
    payload["view_cast"] = view_cast_attrs
    payload["source"] = source_attrs

    print("{}\n".format(json.dumps(payload, sort_keys=True, indent=4, separators=(',', ': '))))

    response = requests.post(
        "https://protograph-staging.pykih.com/api/v1/accounts/ICFJ/datacasts",
        headers={"access_token": "95152504e0fd62376e3bb7984b58a5b03dc132eeecdaa144"},
        json=payload,
    )

    try:
        json.loads(response.text)
    except ValueError:
        with open("error.html", "w") as f:
            f.write(response.text)
        print("Error uploading tweet {}^\n\n".format(row[3]))
        continue

    if "view_cast" in json.loads(response.text):
        successful.append(row[3])
        print("----------- Success^ ----------- \n")
    break
conn.close()

conn = sqlite3.connect("tweet-data/tweet-data.db")
c = conn.cursor()

print(successful)
for each in successful:
    c.execute('''UPDATE tweets
    SET status=1
    where id_str={}'''.format(each))
    conn.commit()
