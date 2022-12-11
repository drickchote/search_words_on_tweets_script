# This script search for multiword expressions (MWE) on twitter
# one thread is open for each MWE
# regex is generated automatically
# this version will search for last 7 days of tweets

import requests
from threading import Lock
import time
import json
import re
import codecs


#  Twitter api allow 450 requests per 15 minutes
MAX_REQUESTS = 450
RELOAD_REQUESTS_TIME_IN_SECONDS = 15 * 60
DAYS_IN_WEEK = 7
from threading import Thread


number_of_requests = 0
initial_time = time.time()


# Words that will be searched
words = [
    'cabra cega',
    'cobra cega',
    'pata cega',
    'gata cega',
    'pe de burro',
    'pé duro',
    'mata rato',
    'olho de peixe',
    'assa peixe',
    'lava bunda',
    'bate bunda',
    'cavalo do cão',
    'coração de boi'
]

base_url = "https://api.twitter.com/2/tweets/search/recent?max_results=100&expansions=geo.place_id&place.fields=name,full_name,place_type&tweet.fields=created_at&query="
lock = Lock()

def init():
    for word in words:
        t =  Thread(target=process_word, args=[word, lock])
        print("starting thread for word: "+word)
        t.start()

def process_word(word, lock):
    global number_of_requests
    
    if(number_of_requests == MAX_REQUESTS):
        time_left = seconds_until_reload_time()
        print("sleeping for "+str(time_left)+" seconds")
        time.sleep(time_left)
        number_of_requests = 0

    tweets = find_tweets(word)
    if len(tweets) > 0:
        file_name = word.replace(" ", "_")+".json"
        file = open(file_name, "a")
        file.write("[")
        for i in range(len(tweets)):
            tweet = {
                "created_at":tweets[i]["created_at"],
                "text": tweets[i]["text"],
                "id":tweets[i]["id"]
            }
            text = json.dumps(tweet)
            if(i < len(tweets) - 1):
                text += ","
            file.write(text)
        file.write("]")

        while lock.locked():
            pass
        lock.acquire(True)
        number_of_requests+=1
        lock.release()
    print("word process finished: "+word)



def seconds_until_reload_time():
    current_time = time.time() 
    execution_time = current_time - initial_time
    result = (RELOAD_REQUESTS_TIME_IN_SECONDS - execution_time) 
    return result if result > 0 else 0


def find_tweets(word):
    url = base_url+word.replace(" ", "%20")
    headers = {
        "Authorization": "Bearer your_twitter_api_key",
        "User-Agent": "curl/7.61.0",
        "Content-Type": "application/json;charset=UTF-8"

    }
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    json = response.json()
    result = []
    if "data" in json and len(json["data"]) > 0:
        for tweet in json["data"]:
            if(is_valid_tweet(word,tweet["text"])):
                result.append(tweet)
    return result

def is_valid_tweet(word, tweet):
    tweet = tweet.lower()
    word = word.lower()
    # generate a regex for an word, example cobra cega = cobra cega|cobra-cega|cobracega
    regex = word + "|"+ word.replace(" ", "-")+ "|"+ word.replace(" ", "") 
    if re.search(regex, tweet) is None:
        return False
    return True



init()
