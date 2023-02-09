# This script search for multiword expressions (MWE) on twitter
# one thread is open for each MWE
# regex is generated automatically
# this version will search for last 7 days of tweets
import unicodedata
import requests
import json
import re



number_of_requests = 180

# Words that will be searched
words = [
# "abalo sísmico",
# "acampamento militar",
# "agente secreto",
# "água doce",
# "água mineral",
# "alarme falso",
# "algodão-doce",
# "alta temporada",
# "alta-costura",
# "alto mar",
# "alto-falante",
# "amigo oculto",
# "amigo secreto",
# "amor-próprio",
# "ano-novo",
# "ar condicionado",
# "ar livre",
# "arma branca",
# "ato falho",
# "banho turco",
# "batata-doce",
# "bebida alcoólica",
# "bode expiatório",
# "braço direito",
# "buraco negro",
# "café colonial",
# "caixa-forte",
# "caixa-preta",
# "caixeiro viajante",
# "câmara fria",
# "carne branca",
# "carne vermelha",
# "carro-forte",
# "carta aberta",
# "centro comercial",
# "centro espírita",
# "cerca viva",
# "céu aberto",
# "cheiro-verde",
# "circuito integrado",
# "círculo vicioso",
# "círculo virtuoso",
# "classe executiva",
# "colégio militar",
# "coluna social",
# "comida caseira",
# "companhia aérea",
# "compound",
# "conta-corrente",
# "coração partido",
# "corda bamba",
# "cordas vocais",
# "curto-circuito",
# "deputado federal",
# "desfile militar",
# "direitos humanos",
# "disco rígido",
# "disco voador",
# "efeito especial",
# "elefante branco",
# "escada rolante",
# "estrela cadente",
# "exame clínico",
# "exame laboratorial",
# "farinha integral",
"febre amarela",
# "ficha limpa",
# "fila indiana",
# "fio condutor",
# "força bruta",
# "gato-pingado",
# "gelo-seco",
# "golpe baixo",
# "governo federal",
# "gripe aviária",
# "gripe suína",
# "guarda-florestal",
# "jogo duro",
# "juízo final",
# "leite integral",
# "lista negra",
# "livre-docente",
# "livro aberto",
# "longa data",
# "longa-metragem",
# "lua cheia",
# "lua nova",
# "lugar-comum",
# "má-fé",
# "magia negra",
# "mão-fechada",
# "máquina virtual",
# "mar aberto",
# "maré alta",
# "maré baixa",
# "massa cinzenta",
# "mau contato",
# "mau-humor",
# "mau-olhado",
# "mercado negro",
# "mesa-redonda",
# "montanha-russa",
# "navio negreiro",
# "nó cego",
# "novo mundo",
# "novo-rico",
# "núcleo atômico",
# "olho gordo",
# "olho mágico",
# "olho nu",
# "ônibus executivo",
# "ovelha negra",
# "pão-duro",
# "papel higiênico",
# "paraíso fiscal",
# "pastor alemão",
# "pau-mandado",
# "pavio curto",
# "pé quente",
# "pé-direito",
# "pé-frio",
# "pente fino",
# "peso morto",
# "planta baixa",
# "poção mágica",
# "pólo-aquático",
# "ponto cego",
# "ponto forte",
# "ponto fraco",
# "prato feito",
# "primeira infância",
# "primeira mão",
# "primeira necessidade",
# "primeira-dama",
# "primeiro ministro",
# "primeiro plano",
# "príncipe encantado",
# "processo seletivo",
# "pronto-socorro",
# "puro-sangue",
# "quadro-negro",
# "queda livre",
# "quinta categoria",
# "rede social",
# "regime político",
# "relógio analógico",
# "relógio biológico",
# "reta final",
# "roda gigante",
# "roleta russa",
# "saia justa",
# "sala cirúrgica",
# "salão paroquial",
# "sangue azul",
# "sangue frio",
# "sangue quente",
# "secretária eletrônica",
# "segundas intenções",
# "segundo plano",
# "sentença judicial",
# "sétima arte",
# "sexto sentido",
# "sinal verde",
# "sistema político",
# "tapete vermelho",
# "tartaruga-marinha",
# "tela plana",
# "tempo real",
# "terceira idade",
# "terceira pessoa",
# "tiro livre",
# "trabalho braçal",
# "trabalho escravo",
# "vaca louca",
# "vinho branco",
# "vinho tinto",
# "vista grossa",
# "viva voz",
# "vôo doméstico",
# "vôo internacional",
# "voto secreto",
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
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAADPZlgEAAAAAmpyFyXI5IHGaZBFRYKnuLnLbXLk%3DtwQbcxQX2SHdFScz7jBxp3wztNg0pP4AOltymXKveU24Ym0zTy",
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

