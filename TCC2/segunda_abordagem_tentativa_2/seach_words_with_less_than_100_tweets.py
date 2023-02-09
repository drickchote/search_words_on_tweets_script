# This script search for multiword expressions (MWE) on twitter
# one thread is open for each MWE
# regex is generated automatically
# this version will search for last 7 days of tweets
import unicodedata
import requests
import json
import re



number_of_requests = 10

# Words that will be searched
words = [
    # "acampamento militar",
    # "banho turco",
    # "caixeiro viajante",
    # "cerca viva",
    # "circuito integrado",
    # "exame laboratorial",
    # "livre-docente",
    # "núcleo atômico",
    # "sala cirúrgica",
    "ônibus executivo"
]

words.sort()

base_url = "https://api.twitter.com/2/tweets/search/all?max_results=500&expansions=geo.place_id&place.fields=name,full_name,place_type&tweet.fields=created_at&query=-is:retweet%20"

def init():
    global number_of_requests

    for word in words:
        url_query = get_query_from_word(word)
        process_word(word, url_query)

# 
# Exemplo: se word = pé-frio |
#   então:  query = "pé-frio"OR"pé frio"OR"pe frio"
def get_query_from_word(word):

    has_hyphen = word.find('-') != -1
    has_accent = len(re.findall(r'[^a-zA-Z\- ]', word)) > 0

    query = "\""+word+"\""

    if has_hyphen:
        subword = word.replace("-", " ")
        query += "OR\""+subword.replace("-", " ")+"\""
    

    if has_accent:
        subword = strip_accents(word.replace("-", " "))
        query += "OR\""+subword.replace("-", " ")+"\""

    return query

def process_word(word, query):
    global number_of_requests
    tweets = find_tweets(query)

    if len(tweets) > 0:
        file_name = str(number_of_requests)+'-'+word.replace(" ", "_")+".json"
        file = open(file_name, "a")
        quantity = len(tweets)
        for i in range(quantity):
            text = generate_json_text(tweets[i], quantity,word,  i == 0, i == quantity-1)
            # text = generate_csv_text(tweets[i])
            file.write(text)

        number_of_requests+=1
    else:
        print("Tweets não encontrados para a palavra "+ word + " e query: "+query)
    # print("word process finished: "+word)

def generate_json_text(tweet,quantity, word, is_fist_tweet = False, is_last_tweet = False, ):
    tweet_object = {
        "created_at":tweet["created_at"],
        "text": tweet["text"],
        "id":tweet["id"]
    }
    tweet_object_text = json.dumps(tweet_object)
    
    if is_fist_tweet:
        print("----- Quantidades para "+word+": "+ str(quantity)+"-----")
        quantity = json.dumps({"tweets_quantity": quantity}) + ","

    start_text = "[" + quantity if is_fist_tweet else ""
    end_text = "]" if is_last_tweet else ","

    result = start_text + tweet_object_text + end_text
    return result

def generate_csv_text(tweet):
    return tweet['id'] + tweet['created_at'] + tweet['text']



def find_tweets(query):
    url = base_url+query
    headers = {
        "Authorization": "Bearer seu_token",
        "User-Agent": "curl/7.61.0",
        "Content-Type": "application/json;charset=UTF-8"

    }
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    json = response.json()

    result = []
    
    if "data" in json:
        result = json["data"]

    return result



def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')


init()

