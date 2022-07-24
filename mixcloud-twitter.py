import requests
import datetime
import twitter_auth
import tweepy
import argparse
import sqlite3
import glob
import os


def mixcloud_uploads(user, interval_seconds):

    feed = requests.get(f'https://api.mixcloud.com/{user}/feed/?limit=50')

    feed_dict = feed.json()

    uploads = [d['cloudcasts'][0] for d in feed_dict['data'] if 'cloudcasts' in d.keys() and d['type'] == 'upload']

    # sort by descending timestamp
    uploads = sorted(uploads, key=lambda k: k['created_time'], reverse=True)

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
    except Exception as e:
        raise e



def main():

    # connect to db
    conn = sqlite3.connect(glob.glob(os.path.dirname(os.path.abspath(__file__)) + '/mixcloud.sqlite3')[0], isolation_level=None)
    cur = conn.cursor()

    # create table if it doesn't exist
    cur.execute('CREATE TABLE IF NOT EXISTS uploads (slug TEXT, timestamp TEXT, tweeted INT)')

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", help="Mixcloud username",
                    type=str)
    parser.add_argument("-i", "--interval", help="Uploads since (seconds)",
                    type=int)
    parser.add_argument("-t", "--text", help="Tweet text. Use {name} and {url} to include upload name and url",
                    type=str, default = "Oi, just uploaded {name} to Mixcloud! \n {url}")

    args = parser.parse_args()

    args.text = args.text.replace('\\n', '\n')



    uploads = mixcloud_uploads(user=args.user, interval_seconds=args.interval)

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

    print("Found " + str(len(uploads)) + " uploads")

    for u in uploads:

        # check if slug in db
        cur.execute('SELECT * FROM uploads WHERE slug = ? AND tweeted=1', (u['slug'],))
        row = cur.fetchall()

        if len(row) == 0:

            print('Tweeting about ' + u['name'] + '...')

            try:
                tweet(text=args.text, upload=u)

                # add to db
                cur.execute('INSERT INTO uploads (slug, timestamp, tweeted) VALUES (?, ?, ?)', (u['slug'], u['created_time'], int(1)))
                conn.commit()
            except Exception as e:
                print(e)
                print('Error tweeting about ' + u['name'])
                continue


if __name__ == "__main__":
    main()

