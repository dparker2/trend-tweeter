from requests_oauthlib import OAuth1Session
from base64 import b64encode
from os import environ, path
from time import sleep, time
from json import loads
from itertools import count
import gpt_2_simple as gpt2

US_WOEID = 23424977
MODEL = "345M"


class TwitterClient(object):
    API = "https://api.twitter.com"
    TWEET_URL = f"{API}/1.1/statuses/update.json"
    TRENDS_URL = f"{API}/1.1/trends/place.json"
    SEARCH_URL = f"{API}/1.1/search/tweets.json"
    GEO_URL = f"{API}/1.1/geo/id/{{}}.json"
    TOKEN_URL = f"{API}/oauth2/token"
    OAUTH_TOKEN_URL = f"{API}/oauth/access_token"

    STREAM = "https://stream.twitter.com"
    FILTER_URL = f"{STREAM}/1.1/statuses/filter.json"

    def __init__(self):
        self.session = OAuth1Session(
            environ["TWITTER_API_KEY"],
            client_secret=environ["TWITTER_API_SECRET"],
            resource_owner_key=environ["TWITTER_TOKEN_ACCESS"],
            resource_owner_secret=environ["TWITTER_TOKEN_SECRET"],
        )

    def stream(self):
        with self.session.get(
            self.FILTER_URL,
            params=dict(
                filter_level="low",
                language="en",
                locations=[-180, -90, 180, 90],  # whole planet
            ),
            stream=True,
        ) as resp:
            for i in resp.iter_lines():
                print(loads(i)["text"])

    def tweet(self, text):
        resp = self.session.post(self.TWEET_URL, params=dict(status=text))
        if resp.status_code != 200:
            raise Exception(resp.text)
        print(resp.text)

    def top_trend(self):
        resp = self.session.get(self.TRENDS_URL, params=dict(id=US_WOEID))
        if resp.status_code != 200:
            raise Exception(resp.text)
        return resp.json()[0]["trends"][0]["name"]


def generate_tweet(prefix):
    if not path.exists(path.join("models", MODEL)):
        gpt2.download_gpt2(model_name=MODEL)
    sess = gpt2.start_tf_sess()
    gpt2.load_gpt2(sess, model_name=MODEL)
    output = gpt2.generate(
        sess,
        prefix=f"{top_trend} ",
        top_k=40,
        return_as_list=True,
        length=240,
        truncate="<|endoftext|>",
        model_name=MODEL,
    )[0]
    return output


def trim_tweet(tweet):
    if len(tweet) <= 240:
        return tweet
    sentences = tweet.split(".")
    for index in range(len(sentences), -1, -1):
        smaller = "".join(f"{sentence}." for sentence in sentences[0:index])
        if len(smaller) <= 240:
            return smaller


if __name__ == "__main__":
    twitter = TwitterClient()
    top_trend = twitter.top_trend()
    print(f"===> Top Trend: {top_trend}")
    tweet = generate_tweet(top_trend).replace("@", "")
    print(f"===> Generated Text: {tweet}")
    trimmed_tweet = trim_tweet(tweet)
    print(f"===> Trimmed Text: {trimmed_tweet}")
    twitter.tweet(trimmed_tweet)
