import tweepy
import datetime
import pandas as pd

# Grabs the follower count for an account
# Updates a local CSV
# Run as cron job every 24 hours


TWITTER_CONSUMER_KEY='1'
TWITTER_CONSUMER_SECRET='2'
TWITTER_ACCESS_TOKEN='3'
TWITTER_ACCESS_TOKEN_SECRET='4'

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

me = api.get_user(screen_name='emojikitchen')
fc = me.followers_count

data = pd.read_csv('follower_data.csv', index_col='date')

now = datetime.datetime.now().date()

data.loc[now] = fc

data.to_csv('follower_data.csv', index='date')
