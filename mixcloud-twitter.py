import requests
import datetime
from dateutil.relativedelta import relativedelta
import twitter_auth
import tweepy
import argparse


def mixcloud_uploads(user, interval_seconds):

    now = datetime.datetime.utcnow()
    then = now - relativedelta(seconds=interval_seconds)
    then_timestamp = then.strftime("%Y-%m-%d %H:%M:%S")

    feed = requests.get(f'https://api.mixcloud.com/{user}/feed?since="{then_timestamp}"', params={'since': then_timestamp})

    feed_dict = feed.json()

    uploads = [d['cloudcasts'][0] for d in feed_dict['data']]

    return uploads


def tweet(text, upload):

    url = upload['url']
    name = upload['name']

    text = text.format(url = url, name = name)

    auth = tweepy.OAuthHandler(twitter_auth.consumer_key, twitter_auth.consumer_secret)

    auth.set_access_token(twitter_auth.access_token, twitter_auth.access_token_secret)

    api = tweepy.API(auth)

    try:
        if api.update_status (text):
            text + '\n' + ("Tweet posted")
    except tweepy.error.TweepError as e:
        text + '\n' + ("Tweet not posted:\n" + str(e))




def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", help="Mixcloud username",
                    type=str)
    parser.add_argument("-i", "--interval", help="Uploads since (seconds)",
                    type=int)
    parser.add_argument("-t", "--text", help="Tweet text. Use {name} and {url} to include upload name and url",
                    type=str)

    args = parser.parse_args()

    try:
        twitter_auth.consumer_key
    except:
        raise Exception('Please set the consumer key in twitter_auth.py')

    try:
        twitter_auth.consumer_secret
    except:
        raise Exception('Please set the consumer secret in twitter_auth.py')

    try:
        twitter_auth.access_token
        twitter_auth.access_token_secret
    except:
        try:
            auth = tweepy.OAuthHandler(twitter_auth.consumer_key, twitter_auth.consumer_secret)
            redirect_url = auth.get_authorization_url()
        except tweepy.TweepError:
            print('Error! Failed to get request token.')
            raise Exception

        print('Please go to ' + str(redirect_url))

        verifier = input('Verifier:')

        auth.request_token = { 'oauth_token' : auth.request_token['oauth_token'],
                         'oauth_token_secret' : verifier}

        try:
            auth.get_access_token(verifier)
        except tweepy.TweepError:
            print('Error! Failed to get access token.')
            raise Exception

        open('twitter_auth.py', 'w').writelines([
            f'access_token = {auth.access_token}',
            f'access_token_secret = {auth.access_token_secret}'
        ])


    uploads = mixcloud_uploads(user=args.user, interval_seconds=args.interval)

    print("Found " + str(len(uploads)) + " uploads")

    for u in uploads:

        print('Tweeting about ' + u['name'] + '...')

        tweet(text=args.text, upload=u)


if __name__ == "__main__":
    main()

