# This script search for multiword expressions (MWE) on twitter
# one thread is open for each MWE
# regex is generated automatically
# this version will search for last 7 days of tweets
import unicodedata




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
    # "gato-pingado",
    # "pé-frio", # remover futebol
    # "pé quente",  # remover futebol
    # "pão-duro", # adicionar pão duro, sem -
    # "sangue azul",
    # "elefante branco",
    "pé-direito",
    # "olho mágico",
    # "olho gordo",
    # "roleta russa",
    # "pau-mandado",
    # "montanha-russa", 
    # "saia justa",
    # "ovelha negra",
    # "bode expiatório",
    # "vista grossa",
    # "sangue frio",
    # "pente fino",
    # "braço direito",
    # "arma branca",
    # "cheiro-verde",
    # "primeira necessidade",
    # "nó cego",
    # "planta baixa",
    # "livro aberto",
    # "pavio curto",
    # "sangue quente",
    # "alta-costura",
    # "peso morto",
    # "pastor alemão",
    # "caixa-preta",
    # "longa-metragem",
    # "quinta categoria",
    # "magia negra",
    # "coração partido",
    # "mercado negro",
    # "mesa-redonda",
    # "reta final",
    # "jogo duro",
    # "fila indiana",
    # "vaca louca",
    # "algodão-doce",
    # "corda bamba",
    # "alto mar",
    # "sinal verde",
    # "lua nova",
    # "sexto sentido",
    # "febre amarela",
    # "água doce",
    # "paraíso fiscal",
    # "ponto forte",
    # "alta temporada",
    # "primeira infância",
    # "lugar-comum",
    # "segundo plano",
    # "puro-sangue",
    # "tiro livre",
    # "fio condutor",
    # "lista negra",
    # "mau contato",
    # "longa data",
    # "céu aberto",
    # "maré baixa",
    # "viva voz",
    # "terceira idade",
    # "má-fé",
    # "príncipe encantado",
    # "ponto cego",
    # "ar livre",
    # "curto-circuito",
    # "mau-olhado",
    # "primeiro plano",
    # "terceira pessoa",
    # "golpe baixo",
    # "alto-falante",
    # "segundas intenções",
    # "relógio biológico",
    # "olho nu",
    # "círculo vicioso",
    # "banho turco",
    # "sétima arte",
    # "ponto fraco",
    # "novo mundo",
    # "cordas vocais",
    # "gelo-seco",
    # "círculo virtuoso",
    # "ar condicionado",
    # "coluna social",
    # "gripe suína",
    # "estrela cadente",
    # "secretária eletrônica",
    # "carro-forte",
    # "livre-docente",
    # "ônibus executivo",
    # "classe executiva",
    # "café colonial",
    # "conta-corrente",
    # "disco rígido",
    # "pronto-socorro",
    # "tempo real",
    # "massa cinzenta",
    # "carne branca",
    # "máquina virtual",
    # "primeira-dama",
    # "pólo-aquático",
    # "buraco negro",
    # "amigo oculto",
    # "disco voador",
    # "quadro-negro",
    # "ficha limpa",
    # "amigo secreto",
    # "companhia aérea",
    # "gripe aviária",
    # "prato feito",
    # "caixa-forte",
    # "alarme falso",
    # "rede social",
    # "poção mágica",
    # "força bruta",
    # "efeito especial",
    # "vinho branco",
    # "vôo doméstico",
    # "centro espírita",
    # "caixeiro viajante",
    # "queda livre",
    # "ato falho",
    # "navio negreiro",
    # "lua cheia",
    # "trabalho braçal",
    # "cerca viva",
    # "juízo final",
    # "novo-rico",
    # "carta aberta",
    # "carne vermelha",
    # "centro comercial",
    # "primeira mão",
    # "tapete vermelho",
    # "mão-fechada",
    # "escada rolante",
    # "direitos humanos",
    # "amor-próprio",
    # "primeiro ministro"
]

base_url = "https://api.twitter.com/2/tweets/search/all?max_results=500&expansions=geo.place_id&place.fields=name,full_name,place_type&tweet.fields=created_at&query=-is:retweet%20"
lock = Lock()

def init():
    for word in words:
        t =  Thread(target=process_word, args=[word, lock])
        print("starting thread for word: "+word)
        t.start()

        has_hyphen = word.find('-')
        has_accent = len(re.findall(r'[^a-zA-Z\-]', word)) > 0

        if has_hyphen:
            subword = word.replace("-", " ")
            t1 =  Thread(target=process_word, args=[subword, lock])
            print("starting thread for word without hyphen : "+subword)
            t1.start()
    
        if has_accent:
            subword = strip_accents(word.replace("-", " "))
            t2 =  Thread(target=process_word, args=[subword, lock])
            print("starting thread for word without hyphen and accent : "+subword)
            t2.start()

def process_word(word, lock):
    global number_of_requests
   
    if(number_of_requests == MAX_REQUESTS):
        time_left = seconds_until_reload_time()
        print("sleeping for "+str(time_left)+" seconds")
        time.sleep(time_left)
        number_of_requests = 0

    tweets = find_tweets(word)
    # tweets = fake_find_tweet()

    if len(tweets) > 0:
        file_name = str(number_of_requests)+'-'+word.replace(" ", "_")+".json"
        file = open(file_name, "a")
        for i in range(len(tweets)):
            text = generate_json_text(tweets[i], i == 0, i == len(tweets)-1)
            # text = generate_csv_text(tweets[i])
            file.write(text)

        while lock.locked():
            pass
        lock.acquire(True)
        number_of_requests+=1
        lock.release()
    print("word process finished: "+word)

def generate_json_text(tweet, is_fist_tweet = False, is_last_tweet = False):
    tweet_object = {
        "created_at":tweet["created_at"],
        "text": tweet["text"],
        "id":tweet["id"]
    }
    tweet_object_text = json.dumps(tweet_object)

    start_text = "[" if is_fist_tweet else ""
    end_text = "]" if is_last_tweet else ","

    result = start_text + tweet_object_text + end_text
    return result

def generate_csv_text(tweet):
    return tweet['id'] + tweet['created_at'] + tweet['text']


def seconds_until_reload_time():
    current_time = time.time() 
    execution_time = current_time - initial_time
    result = (RELOAD_REQUESTS_TIME_IN_SECONDS - execution_time) 
    return result if result > 0 else 0


def find_tweets(word):
    url = base_url+word.replace(" ", "%20")
    headers = {
        "Authorization": "Bearer seu_token",
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

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def fake_find_tweet():
    return [
        {
            "text": "@JanjaLula Mentira. \nMulher pé-frio ! \nVá torcer para o Fluminense.",
            "id": "1623383062812688384",
            "edit_history_tweet_ids": [
                "1623383062812688384"
            ],
            "created_at": "2023-02-08T18:07:37.000Z"
        },
        {
            "text": "a esbanja vai tomar o lugar do mick jagger como pé-frio oficial https://t.co/BAUS4U8o0e",
            "id": "1623361945360338944",
            "edit_history_tweet_ids": [
                "1623361945360338944"
            ],
            "created_at": "2023-02-08T16:43:43.000Z"
        },
        {
            "text": "A tal da Ganja é muito pé-frio. https://t.co/j4AOmRuMfB",
            "id": "1623360369786818561",
            "edit_history_tweet_ids": [
                "1623360369786818561"
            ],
            "created_at": "2023-02-08T16:37:27.000Z"
        },
        {
            "text": "@MonteiroPer1 Baita pé-frio! Faz o L!",
            "id": "1623343570374561793",
            "edit_history_tweet_ids": [
                "1623343570374561793"
            ],
            "created_at": "2023-02-08T15:30:42.000Z"
        },
        {
            "text": "@emerson_rocha E desmistificou essa história do OFF Rio pé-frio. QUe o Vasco venha mais vezes. Já vi até Vasco e Boca aqui! Você que é influente no clube, peça para eles lembrarem mais da gente!",
            "id": "1623339581260066821",
            "edit_history_tweet_ids": [
                "1623339581260066821"
            ],
            "created_at": "2023-02-08T15:14:51.000Z"
        },
        {
            "text": "Mulher de Lula é uma baita pé-frio https://t.co/drMX3aAdb5",
            "id": "1623308670296530944",
            "edit_history_tweet_ids": [
                "1623308670296530944"
            ],
            "created_at": "2023-02-08T13:12:01.000Z"
        },
        {
            "text": "Mundial de Clubes: Torcedora do Flamengo, Janja brinca com a fama de pé-frio\n\nFique por dentro das notícias! Siga @tw_trends_br. Atualizações diárias.\n\n#toptrends #trends #twitter #google\n\n Link da notícia: https://t.co/UDaIMOqAyv",
            "id": "1623305902857105408",
            "edit_history_tweet_ids": [
                "1623305902857105408"
            ],
            "created_at": "2023-02-08T13:01:01.000Z"
        },
        {
            "text": "Janja flamenguista pé-frio https://t.co/drMX3aAdb5",
            "id": "1623289117730643970",
            "edit_history_tweet_ids": [
                "1623289117730643970"
            ],
            "created_at": "2023-02-08T11:54:19.000Z"
        },
        {
            "text": "@samuelvenancio Tô achando que você é pé-frio. Rsss",
            "id": "1623134076130496515",
            "edit_history_tweet_ids": [
                "1623134076130496515"
            ],
            "created_at": "2023-02-08T01:38:14.000Z"
        },
        {
            "geo": {
                "place_id": "63968ec77ab62d12"
            },
            "text": "Pensa num cara pé-frio… https://t.co/140iaQU7Xx",
            "id": "1623127647340359681",
            "edit_history_tweet_ids": [
                "1623127647340359681"
            ],
            "created_at": "2023-02-08T01:12:42.000Z"
        },
        {
            "text": "Eis o motivo da \"DERROTA DOS MULAMBIS\".\n😅🤣😅🤣😅🤣😅🤣😅🤣😅🤣😅🤣😅🤣😅🤣\n#Janja Pé-frio https://t.co/CkNFclS5F1",
            "id": "1623126460012679169",
            "edit_history_tweet_ids": [
                "1623126460012679169"
            ],
            "created_at": "2023-02-08T01:07:58.000Z"
        },
        {
            "text": "@UmFlamenguistta A maldita Janja pé-frio",
            "id": "1623110199623008256",
            "edit_history_tweet_ids": [
                "1623110199623008256"
            ],
            "created_at": "2023-02-08T00:03:22.000Z"
        },
        {
            "text": "Canja pé-frio lazarento. Fod o Brasil, Fod o Flamengo. https://t.co/esKiaNirU0",
            "id": "1623105243176116225",
            "edit_history_tweet_ids": [
                "1623105243176116225"
            ],
            "created_at": "2023-02-07T23:43:40.000Z"
        },
        {
            "text": "@gugachacra É, Guga, continua torcendo só pelo porco mesmo. Se foi sincero seu apoio, vc é um tremendo pé-frio!",
            "id": "1623099988199759873",
            "edit_history_tweet_ids": [
                "1623099988199759873"
            ],
            "created_at": "2023-02-07T23:22:47.000Z"
        },
        {
            "text": "@Damadeferroofic Pegou fama de pé-frio, não vai conseguir ir num jogo nunca mais",
            "id": "1623094323511234561",
            "edit_history_tweet_ids": [
                "1623094323511234561"
            ],
            "created_at": "2023-02-07T23:00:17.000Z"
        },
        {
            "text": "@UrubuTT_ Janja, pé-frio",
            "id": "1623093714171183104",
            "edit_history_tweet_ids": [
                "1623093714171183104"
            ],
            "created_at": "2023-02-07T22:57:51.000Z"
        },
        {
            "text": "@galvaobueno @buenowines coloca um vinho debaixo do pé que sai geladinho \n\ngalvão pé-frio!!!\n\ne passa o endereço da fazenda pra organizar o proximo churrasco e confraternização do MST",
            "id": "1623092260068896770",
            "edit_history_tweet_ids": [
                "1623092260068896770"
            ],
            "created_at": "2023-02-07T22:52:05.000Z"
        },
        {
            "text": "@Flamengo A Canja estava assistindo. Vai ser pé-frio assim lá na PQP!",
            "id": "1623085663783464963",
            "edit_history_tweet_ids": [
                "1623085663783464963"
            ],
            "created_at": "2023-02-07T22:25:52.000Z"
        },
        {
            "text": "Mundial de Clubes: Torcedora do Flamengo, Janja brinca com a fama de pé-frio https://t.co/tEm4XTRqLe",
            "id": "1623083325895376897",
            "edit_history_tweet_ids": [
                "1623083325895376897"
            ],
            "created_at": "2023-02-07T22:16:34.000Z"
        },
        {
            "text": "Mundial de Clubes: Torcedora do Flamengo, Janja brinca com a fama de pé-frio https://t.co/zYEZoOqTrY",
            "id": "1623082944804843521",
            "edit_history_tweet_ids": [
                "1623082944804843521"
            ],
            "created_at": "2023-02-07T22:15:04.000Z"
        },
        {
            "text": "Mundial de Clubes: Torcedora do Flamengo, Janja brinca com a fama de pé-frio https://t.co/Fq1a8T2WrJ",
            "id": "1623082941512400897",
            "edit_history_tweet_ids": [
                "1623082941512400897"
            ],
            "created_at": "2023-02-07T22:15:03.000Z"
        },
        {
            "text": "Qual dos dois é mais pé-frio ?? https://t.co/CL07Tr2EN6 https://t.co/UZpg0ZT3Zp",
            "id": "1623080918599577605",
            "edit_history_tweet_ids": [
                "1623080918599577605"
            ],
            "created_at": "2023-02-07T22:07:01.000Z"
        },
        {
            "text": "@APalpites Que esse portuga é pé-frio nem discuto.\nAgora , tirar um comando vitorioso e botar novatos na direção com 3 taças em disputa logo no 1o mes queima qq um.",
            "id": "1623072451822292996",
            "edit_history_tweet_ids": [
                "1623072451822292996"
            ],
            "created_at": "2023-02-07T21:33:22.000Z"
        },
        {
            "text": "@flferronato A Canja pode ser pé-frio ou quente;de qualquer forma 🙏🙏🙏 logo estaremos definitivamente livres do Dilmo e de tudo de ruim que ele representa.O tempo está se encarregando disso.Á cada dia que passa,ele não fica mais jovem...",
            "id": "1623069873231343617",
            "edit_history_tweet_ids": [
                "1623069873231343617"
            ],
            "created_at": "2023-02-07T21:23:07.000Z"
        },
        {
            "text": "@DoougFuny Tu é muito pé-frio, haha",
            "id": "1623063585466519554",
            "edit_history_tweet_ids": [
                "1623063585466519554"
            ],
            "created_at": "2023-02-07T20:58:08.000Z"
        },
        {
            "text": "@AndradeRNegro3 É 6º jogo do cara, com Arrasca mal (depende muito dele) zaga terrível e pixotadas do Gérson e Matheuzinho. O menor culpado é ele. O maior é a diretoria, que demitiu Dorival á vesperas do Mundial. Alguém sabe o porque?  Melhor apelar pra superstição e dizer que o Vítor é pé-frio.",
            "id": "1623061130058039299",
            "edit_history_tweet_ids": [
                "1623061130058039299"
            ],
            "created_at": "2023-02-07T20:48:23.000Z"
        },
        {
            "text": "@10Ronaldinho @Flamengo Pé-frio",
            "id": "1623060491080978433",
            "edit_history_tweet_ids": [
                "1623060491080978433"
            ],
            "created_at": "2023-02-07T20:45:50.000Z"
        },
        {
            "text": "Al Hilal ganhando do Flamengo. O governador afastado do DF e pé-frio de primeira omissão Ibaneis Rocha deve tá  no Marrocos!!! Só pode!!!",
            "id": "1623050940675723273",
            "edit_history_tweet_ids": [
                "1623050940675723273"
            ],
            "created_at": "2023-02-07T20:07:53.000Z"
        },
        {
            "text": "@lactocecilias Desta vez, eu não sou o pé-frio pq não tô vendo o jogo.",
            "id": "1623036668264517636",
            "edit_history_tweet_ids": [
                "1623036668264517636"
            ],
            "created_at": "2023-02-07T19:11:10.000Z"
        },
        {
            "text": "Vamos se a Variety continua mantendo a tradição de ser a revista mais Pé-Frio do mundo ou se acertou suas previsões dos ganhadores nesse Grammy 2023:\n\nAoty: Renaissance (Errou)❌;\nRoty: As It Was (Errou)❌;\nSoty: As It Was (Errou)❌;\nBna: Anitta (Errou)❌. https://t.co/qTZD7iM4xW",
            "id": "1622980841839157249",
            "edit_history_tweet_ids": [
                "1622980841839157249"
            ],
            "created_at": "2023-02-07T15:29:20.000Z"
        },
        {
            "text": "Só observo o pé-frio dessa rede social desde a Marcela no 20... https://t.co/5uhkOd4pXY",
            "id": "1622784355616669697",
            "edit_history_tweet_ids": [
                "1622784355616669697"
            ],
            "created_at": "2023-02-07T02:28:34.000Z"
        },
        {
            "text": "@comentacali @vulgofop Ele é pé-frio?",
            "id": "1622435888478228482",
            "edit_history_tweet_ids": [
                "1622435888478228482"
            ],
            "created_at": "2023-02-06T03:23:53.000Z"
        },
        {
            "text": "Com fama de pé-frio, irmã de Gabigol anuncia decisão sobre o Mundial https://t.co/rTOXMAg9LC",
            "id": "1622055130374836224",
            "edit_history_tweet_ids": [
                "1622055130374836224"
            ],
            "created_at": "2023-02-05T02:10:54.000Z"
        },
        {
            "text": "Com fama de pé-frio, irmã de Gabigol anuncia decisão sobre o Mundial https://t.co/dBfqk9m2kj",
            "id": "1622042422191525890",
            "edit_history_tweet_ids": [
                "1622042422191525890"
            ],
            "created_at": "2023-02-05T01:20:24.000Z"
        },
        {
            "text": "Com fama de pé-frio, irmã de Gabigol anuncia decisão sobre o Mundial\n\nhttps://t.co/HbsBR9xxXb",
            "id": "1622010941033390085",
            "edit_history_tweet_ids": [
                "1622010941033390085"
            ],
            "created_at": "2023-02-04T23:15:18.000Z"
        },
        {
            "text": "@elonmusk quer inveja está ninguém deixa eu ter nada desgraça de família pé-frio morte de raiva",
            "id": "1621824505386500096",
            "edit_history_tweet_ids": [
                "1621824505386500096"
            ],
            "created_at": "2023-02-04T10:54:28.000Z"
        },
        {
            "text": "O lado que apoia a siência. O presidente não é pé-frio, por isso o dólar caiu. Teve nada a ver com China não e valorização das moedas emergentes, é que o magnânimo Loole é sortudo, gente! Olha que maravilha https://t.co/AD4fka6O9P",
            "id": "1621541250460692481",
            "edit_history_tweet_ids": [
                "1621541250460692481"
            ],
            "created_at": "2023-02-03T16:08:55.000Z"
        },
        {
            "text": "@jairbolsonaro Mais de 30 milhões de brasileiros passando fome. Seu governo foi o pior da história. \nQue nunca mais tenhamos um presidente tão pé-frio    e incompetente. \nO Brasil agora vai avançar.",
            "id": "1621535399263731714",
            "edit_history_tweet_ids": [
                "1621535399263731714"
            ],
            "created_at": "2023-02-03T15:45:40.000Z"
        },
        {
            "text": "@LuizPersechini Mesmo que seja sorte,\n\nMelhor um presidente com sorte que um pé-frio, não? Sucesso é sucesso, seja acidental ou não.",
            "id": "1621478466272038914",
            "edit_history_tweet_ids": [
                "1621478466272038914"
            ],
            "created_at": "2023-02-03T11:59:26.000Z"
        },
        {
            "text": "Dona Irene e o pé-frio https://t.co/hGAmVsFbWO",
            "id": "1621263322287841281",
            "edit_history_tweet_ids": [
                "1621263322287841281"
            ],
            "created_at": "2023-02-02T21:44:32.000Z"
        },
        {
            "text": "Dona Irene e o pé-frio. https://t.co/OP7wzWX2BP",
            "id": "1621263273004879872",
            "edit_history_tweet_ids": [
                "1621263273004879872"
            ],
            "created_at": "2023-02-02T21:44:20.000Z"
        },
        {
            "geo": {
                "place_id": "a4ddc3856053f7e1"
            },
            "text": "@OGloboPolitica Micheque é pé-frio🙃",
            "id": "1621078013877321728",
            "edit_history_tweet_ids": [
                "1621078013877321728"
            ],
            "created_at": "2023-02-02T09:28:11.000Z"
        },
        {
            "text": "“Sua primeira agenda no país começou com fama de pé-frio” PERDEU MANÉ https://t.co/1XOkY4AXD4",
            "id": "1620903225313607681",
            "edit_history_tweet_ids": [
                "1620903225313607681"
            ],
            "created_at": "2023-02-01T21:53:38.000Z"
        },
        {
            "text": "A derrota de @rogeriosmarinho aquece a máxima recente que o senador @ciro_nogueira anda carregado de “pé-frio”. A fama vai ficando forte e cai no anedotário nacional. https://t.co/R5Xxd3BMX7",
            "id": "1620899360211968012",
            "edit_history_tweet_ids": [
                "1620899360211968012"
            ],
            "created_at": "2023-02-01T21:38:16.000Z"
        },
        {
            "text": "Perception: Marinho presidente do senado\nReality: Bolsonaro pé-frio",
            "id": "1620899164774367232",
            "edit_history_tweet_ids": [
                "1620899164774367232"
            ],
            "created_at": "2023-02-01T21:37:30.000Z"
        },
        {
            "text": "nossa, mas o titica de maringá é muito pé-frio...\n\nnum dá uma dentro, pô!",
            "id": "1620896916769841156",
            "edit_history_tweet_ids": [
                "1620896916769841156"
            ],
            "created_at": "2023-02-01T21:28:34.000Z"
        },
        {
            "text": "O Pilantra do Silas tá mais pé-frio que o Prefeitão! Hahahahah https://t.co/iRCw6YO1M9",
            "id": "1620895117312946176",
            "edit_history_tweet_ids": [
                "1620895117312946176"
            ],
            "created_at": "2023-02-01T21:21:25.000Z"
        },
        {
            "text": "Caralho kkkkkkkkkkkkk.\n\nIncrível o quão PÉ-FRIO é esse time.\n\nRepelente de Champions League. Nanico. https://t.co/WxtqOvRjnU",
            "id": "1620894875859439617",
            "edit_history_tweet_ids": [
                "1620894875859439617"
            ],
            "created_at": "2023-02-01T21:20:27.000Z"
        },
        {
            "text": "@Infos_palestra Não gosto em como o Abel fala da arbitragem, porém, é compreensível de alguém que se entrega naquilo que faz. Ver jornalista falar o que falou dele é inacreditável! Muricy passou por isso aqui e Telê então com a fama de pé-frio... mas há mta proteção para os treinadores \"amigos\".",
            "id": "1620807151500529666",
            "edit_history_tweet_ids": [
                "1620807151500529666"
            ],
            "created_at": "2023-02-01T15:31:52.000Z"
        },
        {
            "text": "Esse Jorginho fede a jogador fracassado, pé-frio, perdedor e que mina o ambiente.\n\npqp\n\nExatamente o tipo de jogador que o Arsenal não precisava.",
            "id": "1620520236645773313",
            "edit_history_tweet_ids": [
                "1620520236645773313"
            ],
            "created_at": "2023-01-31T20:31:46.000Z"
        },
        {
            "text": "@CuttieFlam_ eu fui abrir na radio cbn pra acompanhar, perdeu\npé-frio, vou nem mais ver o jogo KEKW",
            "id": "1620221824272318464",
            "edit_history_tweet_ids": [
                "1620221824272318464"
            ],
            "created_at": "2023-01-31T00:45:59.000Z"
        },
        {
            "text": "@dariojjunior Com a Canja pé-frio não dá",
            "id": "1620171531493191683",
            "edit_history_tweet_ids": [
                "1620171531493191683"
            ],
            "created_at": "2023-01-30T21:26:09.000Z"
        },
        {
            "text": "Além de tudo é pé-frio! https://t.co/PUnfNKOpgj",
            "id": "1620135663923531778",
            "edit_history_tweet_ids": [
                "1620135663923531778"
            ],
            "created_at": "2023-01-30T19:03:37.000Z"
        },
        {
            "text": "Queria pedir desculpas pra toda nação de torcedores dos 49ers no Brasil.\n\nInfelizmente não consegui gravar o @thegoldrushbr na semana passada e assumo total responsabilidade pelo desastre de ontem.\n\nEu jamais poderia ter deixado a pé-frio da @NinersNewsBR assumir o meu lugar. https://t.co/b3kThFsGFh",
            "id": "1620074996512215042",
            "edit_history_tweet_ids": [
                "1620074996512215042"
            ],
            "created_at": "2023-01-30T15:02:33.000Z"
        },
        {
            "text": "Mulher pé-frio ajudando na derrota do Flamengo ! A cara da derrota em pessoa https://t.co/PjKBkSoE59",
            "id": "1620060353865584641",
            "edit_history_tweet_ids": [
                "1620060353865584641"
            ],
            "created_at": "2023-01-30T14:04:22.000Z"
        },
        {
            "text": "@revistaoeste Pé-frio, como todo PETISTA.\n#ForaLula \n#PachecoNAO",
            "id": "1620035481412210690",
            "edit_history_tweet_ids": [
                "1620035481412210690"
            ],
            "created_at": "2023-01-30T12:25:32.000Z"
        },
        {
            "text": "Da maldição do terceiro uniforme, passamos para o pé-frio da primeira-dama. Fala sério. https://t.co/ni7rZbzL4o",
            "id": "1620012111282716674",
            "edit_history_tweet_ids": [
                "1620012111282716674"
            ],
            "created_at": "2023-01-30T10:52:40.000Z"
        },
        {
            "text": "Gente,\n\nQue diferença hein?\nA #canja foi no jogo do Flamengo hoje, mas tá igual ao Mick Jagger, tremendo pé-frio, Flamengo perdeu.\n\nPergunta que não quer calar:\nPq será que o Luladrao não foi ao jogo? 🤔🤔 https://t.co/XFpZ1I6lzO",
            "id": "1619943967629639680",
            "edit_history_tweet_ids": [
                "1619943967629639680"
            ],
            "created_at": "2023-01-30T06:21:53.000Z"
        },
        {
            "text": "@Vessoni VP era incompetente ou pé-frio?\nOu um pouquinho se cada?\n🤣🤣🤣",
            "id": "1619883654611869696",
            "edit_history_tweet_ids": [
                "1619883654611869696"
            ],
            "created_at": "2023-01-30T02:22:13.000Z"
        },
        {
            "text": "@medicinaupap pé-frio.",
            "id": "1619855257634496512",
            "edit_history_tweet_ids": [
                "1619855257634496512"
            ],
            "created_at": "2023-01-30T00:29:23.000Z"
        },
        {
            "text": "Mesmo gostando do Mahomes, queria muito ver Joe Burrow no SuperBowl. Mas, como sempre sou pé-frio ao extremo, deve dar Chiefs\n\n#NFLnaESPN #CINvsKC #ChiefsKingdom #RuleTheJungle",
            "id": "1619855030315786240",
            "edit_history_tweet_ids": [
                "1619855030315786240"
            ],
            "created_at": "2023-01-30T00:28:29.000Z"
        },
        {
            "text": "@mahagess Foi banida por ser pé-frio",
            "id": "1619843509665828865",
            "edit_history_tweet_ids": [
                "1619843509665828865"
            ],
            "created_at": "2023-01-29T23:42:42.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo e torcedores a chamam de pé-frio\nhttps://t.co/xAfOyzuCxM",
            "id": "1619840590996447238",
            "edit_history_tweet_ids": [
                "1619840590996447238"
            ],
            "created_at": "2023-01-29T23:31:06.000Z"
        },
        {
            "text": "Janja assiste vice do Flamengo e torcida a chama de pé-frio https://t.co/JFTO8d0zal",
            "id": "1619808292514979841",
            "edit_history_tweet_ids": [
                "1619808292514979841"
            ],
            "created_at": "2023-01-29T21:22:46.000Z"
        },
        {
            "text": "@tecsuper @FluJedssantos Pé-frio dos infernos !\n#PachecoNao",
            "id": "1619803335011483648",
            "edit_history_tweet_ids": [
                "1619803335011483648"
            ],
            "created_at": "2023-01-29T21:03:04.000Z"
        },
        {
            "text": "Janja assiste vice do Flamengo e torcida a chama de pé-frio https://t.co/ZUrqGMPflm",
            "id": "1619803112570773504",
            "edit_history_tweet_ids": [
                "1619803112570773504"
            ],
            "created_at": "2023-01-29T21:02:11.000Z"
        },
        {
            "text": "Sua presença no revés do clube de coração já está lhe rendendo até alguns apelidos, como 'Mick Janja', em alusão ao cantor e compositor Mick Jagger, que tem fama de pé-frio em suas ‘escolhas e torcidas’ no esporte. https://t.co/K4m5Y7sPMs",
            "id": "1619796063703146496",
            "edit_history_tweet_ids": [
                "1619796063703146496"
            ],
            "created_at": "2023-01-29T20:34:10.000Z"
        },
        {
            "text": "Com fama de pé-frio no SBT, Neila Medeiros dá a volta por cima na Record &gt; \nhttps://t.co/GbvC1lUqar https://t.co/wzK1ywIbaP",
            "id": "1619787617062592513",
            "edit_history_tweet_ids": [
                "1619787617062592513"
            ],
            "created_at": "2023-01-29T20:00:36.000Z"
        },
        {
            "text": "@ATROMBETA3 Além de feia é pé-frio. Só podia ser mulher do cachaceiro",
            "id": "1619784745516404737",
            "edit_history_tweet_ids": [
                "1619784745516404737"
            ],
            "created_at": "2023-01-29T19:49:12.000Z"
        },
        {
            "text": "@feels_jkchild @luciana_onofre Entendi. \n\nMas ela não é \"pe-frio\"",
            "id": "1619777670350520320",
            "edit_history_tweet_ids": [
                "1619777670350520320"
            ],
            "created_at": "2023-01-29T19:21:05.000Z"
        },
        {
            "text": "@revistaoeste Hahaha baranga pé-frio de merda!!!",
            "id": "1619776148652818432",
            "edit_history_tweet_ids": [
                "1619776148652818432"
            ],
            "created_at": "2023-01-29T19:15:02.000Z"
        },
        {
            "text": "em alusão ao cantor e compositor Mick Jagger, que tem fama de pé-frio em suas ‘escolhas e torcidas’ no esporte. ⏬ https://t.co/LyWv5ix4ya",
            "id": "1619769647456473090",
            "edit_history_tweet_ids": [
                "1619769647456473090"
            ],
            "created_at": "2023-01-29T18:49:12.000Z"
        },
        {
            "text": "Será que o pé-frio do Rob McElhenney já viu alguma vitória no estádio?? Hoje, mais uma vez, só está o Ryan Reynolds! #FACupNaESPN",
            "id": "1619764449480671232",
            "edit_history_tweet_ids": [
                "1619764449480671232"
            ],
            "created_at": "2023-01-29T18:28:33.000Z"
        },
        {
            "text": "@folha Pode ser pé-frio, mas aceita o resultado.Já outros ,não .",
            "id": "1619748573574463489",
            "edit_history_tweet_ids": [
                "1619748573574463489"
            ],
            "created_at": "2023-01-29T17:25:28.000Z"
        },
        {
            "text": "@Marcostelecom28 @Vladrodrigues @TimeFlamengo @Gkroll1 Pelo que dizem… \nE parece ser pé-frio né? Largou o basquete para ir para Brasília e deu no que deu… https://t.co/SoeYHrHFwO",
            "id": "1619745909356781568",
            "edit_history_tweet_ids": [
                "1619745909356781568"
            ],
            "created_at": "2023-01-29T17:14:52.000Z"
        },
        {
            "text": "Tenho certeza que a Janja foi a culpada pela derrota do Flamengo ontem.\n\nNão tem outra explicação. \n\nPé-Frio! LAZARENTA!\n\nFlamengo muito superior ao Palmeiras. https://t.co/oM2OMzb0E7",
            "id": "1619736242580766720",
            "edit_history_tweet_ids": [
                "1619736242580766720"
            ],
            "created_at": "2023-01-29T16:36:28.000Z"
        },
        {
            "text": "@JanjaLula assiste jogo do Flamengo na Supercopa, dá azar e Flamengo perde para o Palmeiras, torcedores a chamam de pé-frio*\n*#COMPARTILHE*\n\n*https://t.co/zCuowxiciy*\n\n*PARTICIPE DO NOSSO GRUPO NO WHATSAPP:* ✅🇧🇷 https://t.co/p5hmuiJvWH",
            "id": "1619715373603131394",
            "edit_history_tweet_ids": [
                "1619715373603131394"
            ],
            "created_at": "2023-01-29T15:13:32.000Z"
        },
        {
            "text": "@dennesousa1 Ela não é só pé-frio. É um encosto mesmo!",
            "id": "1619713708242145281",
            "edit_history_tweet_ids": [
                "1619713708242145281"
            ],
            "created_at": "2023-01-29T15:06:55.000Z"
        },
        {
            "text": "Canja assiste jogo do Flamengo na Supercopa, dá azar e Flamengo perde para o Palmeiras, torcedores a chamam de pé-frio. https://t.co/v9sDSUXmnY",
            "id": "1619709125625282560",
            "edit_history_tweet_ids": [
                "1619709125625282560"
            ],
            "created_at": "2023-01-29T14:48:42.000Z"
        },
        {
            "text": "@ATROMBETA3 Janja cafona e pé-frio...",
            "id": "1619707849583788034",
            "edit_history_tweet_ids": [
                "1619707849583788034"
            ],
            "created_at": "2023-01-29T14:43:38.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio\nhttps://t.co/c57RQFs67u",
            "id": "1619705410105249792",
            "edit_history_tweet_ids": [
                "1619705410105249792"
            ],
            "created_at": "2023-01-29T14:33:57.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/jrsZ13gfyL",
            "id": "1619698923073052675",
            "edit_history_tweet_ids": [
                "1619698923073052675"
            ],
            "created_at": "2023-01-29T14:08:10.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo e torcedores a chamam de pé-frio https://t.co/nGqFOOhdmP",
            "id": "1619685288481259520",
            "edit_history_tweet_ids": [
                "1619685288481259520"
            ],
            "created_at": "2023-01-29T13:13:59.000Z"
        },
        {
            "text": "Janja assiste jogo do Flamengo na Supercopa, dá azar e Flamengo perde para o Palmeiras, torcedores a chamam de pé-frio https://t.co/Shg5cA8HpN",
            "id": "1619678192016703493",
            "edit_history_tweet_ids": [
                "1619678192016703493"
            ],
            "created_at": "2023-01-29T12:45:47.000Z"
        },
        {
            "text": "@oiIuiz Além de feia é pé-frio.",
            "id": "1619674554405916674",
            "edit_history_tweet_ids": [
                "1619674554405916674"
            ],
            "created_at": "2023-01-29T12:31:20.000Z"
        },
        {
            "geo": {
                "place_id": "5722ff20ba67083b"
            },
            "text": "@folha Pé-frio é a mídia golpista que torceu pelo bozo e se ferrou...",
            "id": "1619672427247865861",
            "edit_history_tweet_ids": [
                "1619672427247865861"
            ],
            "created_at": "2023-01-29T12:22:53.000Z"
        },
        {
            "text": "@JoaquinTeixeira Janja vai torcer para outro time, só ir e o Mengão perde. Pé-frio.\n\nJanja Mick Jagger vai torcer pra o @ibismania",
            "id": "1619650981377064961",
            "edit_history_tweet_ids": [
                "1619650981377064961"
            ],
            "created_at": "2023-01-29T10:57:40.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/jggGFMFHDH https://t.co/Qqo93jox4r",
            "id": "1619638346799620096",
            "edit_history_tweet_ids": [
                "1619638346799620096"
            ],
            "created_at": "2023-01-29T10:07:27.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/gZBd0JYznV https://t.co/8uh7NMAOgf",
            "id": "1619635679624921090",
            "edit_history_tweet_ids": [
                "1619635679624921090"
            ],
            "created_at": "2023-01-29T09:56:52.000Z"
        },
        {
            "text": "@folha Putz vai virar tablóide de fofocas agora, é uma vergonha, o que é ser pé-frio no jogo para quem ajudou o marido a ganhar a presidência. De pé-frio ela não tem nada.",
            "id": "1619630416922808321",
            "edit_history_tweet_ids": [
                "1619630416922808321"
            ],
            "created_at": "2023-01-29T09:35:57.000Z"
        },
        {
            "text": "@oiIuiz A JANJA CORRIMAO ALEM DE TUDO E PE-FRIO AZARADO",
            "id": "1619547037435060224",
            "edit_history_tweet_ids": [
                "1619547037435060224"
            ],
            "created_at": "2023-01-29T04:04:38.000Z"
        },
        {
            "text": "@Paullo_Gustavo Pé-frio do baralho...",
            "id": "1619540502017359874",
            "edit_history_tweet_ids": [
                "1619540502017359874"
            ],
            "created_at": "2023-01-29T03:38:39.000Z"
        },
        {
            "text": "@teojose Janja pé-frio 🦶🥶  😂😂😂😂😂",
            "id": "1619540010625290241",
            "edit_history_tweet_ids": [
                "1619540010625290241"
            ],
            "created_at": "2023-01-29T03:36:42.000Z"
        },
        {
            "text": "@JanjaLula quem pagou essa viagem? \nJanja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/C1MQDGcyKu",
            "id": "1619536889039720450",
            "edit_history_tweet_ids": [
                "1619536889039720450"
            ],
            "created_at": "2023-01-29T03:24:18.000Z"
        },
        {
            "text": "@fl4pires Pé-frio do baralho... https://t.co/ERlQ7hi2j3",
            "id": "1619531633706799105",
            "edit_history_tweet_ids": [
                "1619531633706799105"
            ],
            "created_at": "2023-01-29T03:03:25.000Z"
        },
        {
            "text": "@futebol_info Pé-frio do kct. Mulher de bandido.",
            "id": "1619519200137183232",
            "edit_history_tweet_ids": [
                "1619519200137183232"
            ],
            "created_at": "2023-01-29T02:14:01.000Z"
        },
        {
            "text": "@folha Canja pé-frio",
            "id": "1619518051837423618",
            "edit_history_tweet_ids": [
                "1619518051837423618"
            ],
            "created_at": "2023-01-29T02:09:27.000Z"
        },
        {
            "text": "@Binhosampas Além de tudo, ainda é pé-frio. 🦶🥶",
            "id": "1619510847294017536",
            "edit_history_tweet_ids": [
                "1619510847294017536"
            ],
            "created_at": "2023-01-29T01:40:49.000Z"
        },
        {
            "text": "Xanxa pé-frio. https://t.co/KVQ5cPpa9p",
            "id": "1619509643361021952",
            "edit_history_tweet_ids": [
                "1619509643361021952"
            ],
            "created_at": "2023-01-29T01:36:02.000Z"
        },
        {
            "text": "Não acho que foi pé-frio de ninguém, foi lá-e-cá, pé-frio se fosse de goleada.\n\n(por porco não foi goleada😂)\n\n(eu dei uma esgoelada😂)\n\n💚🐷⚽🐷💚",
            "id": "1619498449959006208",
            "edit_history_tweet_ids": [
                "1619498449959006208"
            ],
            "created_at": "2023-01-29T00:51:33.000Z"
        },
        {
            "text": "@brunocvieira12 @Miltonneves Canja é pé-frio!!! 🤮🤮",
            "id": "1619492750411591680",
            "edit_history_tweet_ids": [
                "1619492750411591680"
            ],
            "created_at": "2023-01-29T00:28:55.000Z"
        },
        {
            "geo": {
                "place_id": "f7d4e4d80ee8125b"
            },
            "text": "“Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio”\nMais do mesmo. Nem precisa de mãe Diná.",
            "id": "1619491849353453569",
            "edit_history_tweet_ids": [
                "1619491849353453569"
            ],
            "created_at": "2023-01-29T00:25:20.000Z"
        },
        {
            "text": "Manchete principal: Janja é chamada de pé-frio após Flamengo perder Supercopa - 28/01/2023 - Celebridades - F5 https://t.co/vhtBQx4H60, see more https://t.co/MrYNPcWyLQ",
            "id": "1619488967623168000",
            "edit_history_tweet_ids": [
                "1619488967623168000"
            ],
            "created_at": "2023-01-29T00:13:53.000Z"
        },
        {
            "text": "por ser pé-frio, obviamente",
            "id": "1619487028131033093",
            "edit_history_tweet_ids": [
                "1619487028131033093"
            ],
            "created_at": "2023-01-29T00:06:10.000Z"
        },
        {
            "text": "@gicamonteiro Canja é pé-frio..ahahah",
            "id": "1619486737499316224",
            "edit_history_tweet_ids": [
                "1619486737499316224"
            ],
            "created_at": "2023-01-29T00:05:01.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/P1IckHsvV9",
            "id": "1619478703536488448",
            "edit_history_tweet_ids": [
                "1619478703536488448"
            ],
            "created_at": "2023-01-28T23:33:06.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/KGh8qwRSCJ",
            "id": "1619474411551088640",
            "edit_history_tweet_ids": [
                "1619474411551088640"
            ],
            "created_at": "2023-01-28T23:16:02.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/aiD35UZXe8",
            "id": "1619474175873396736",
            "edit_history_tweet_ids": [
                "1619474175873396736"
            ],
            "created_at": "2023-01-28T23:15:06.000Z"
        },
        {
            "text": "Janja assiste derrota do Flamengo na Supercopa e torcedores a chamam de pé-frio https://t.co/SoUf6bASfH",
            "id": "1619474163034382339",
            "edit_history_tweet_ids": [
                "1619474163034382339"
            ],
            "created_at": "2023-01-28T23:15:03.000Z"
        },
        {
            "text": "Olha o pé-frio aí https://t.co/3B32oikBwj",
            "id": "1619468519288221699",
            "edit_history_tweet_ids": [
                "1619468519288221699"
            ],
            "created_at": "2023-01-28T22:52:37.000Z"
        },
        {
            "text": "@JoaquinTeixeira Pé-frio sem-vergonh@",
            "id": "1619466480071974914",
            "edit_history_tweet_ids": [
                "1619466480071974914"
            ],
            "created_at": "2023-01-28T22:44:31.000Z"
        },
        {
            "text": "@Paullo_Gustavo Pé-frio isso sim,",
            "id": "1619464989215195136",
            "edit_history_tweet_ids": [
                "1619464989215195136"
            ],
            "created_at": "2023-01-28T22:38:36.000Z"
        },
        {
            "text": "@choquei @Metropoles Ela não é Pé-Frio;é \"Pé-Jangelado\"!!!rsrsrs",
            "id": "1619462064468299776",
            "edit_history_tweet_ids": [
                "1619462064468299776"
            ],
            "created_at": "2023-01-28T22:26:58.000Z"
        },
        {
            "text": "@ColunadoFla \nEssa qua/dri/lha ainda por cima é pé-frio. Com essa personalidade nefasta, não tem jeito. Atrai só o que é ruim.Espero que tenham aprendido a lição. Parem de bater palma para a qua(dri)lha dançar. \n#Flamengo \n@Flamengo_en https://t.co/7VASXHxeOZ",
            "id": "1619456005481308160",
            "edit_history_tweet_ids": [
                "1619456005481308160"
            ],
            "created_at": "2023-01-28T22:02:54.000Z"
        },
        {
            "text": "Não tinha como o Flamengo ganhar! Sai CoisoNaro, entra outro pé-frio. \nSó faltou Mick Jagger!!! ❤️🖤 https://t.co/uwdjiYJRWH",
            "id": "1619454823417671681",
            "edit_history_tweet_ids": [
                "1619454823417671681"
            ],
            "created_at": "2023-01-28T21:58:12.000Z"
        },
        {
            "text": "Pé-frio https://t.co/UNIPgDdkRs",
            "id": "1619453502316740608",
            "edit_history_tweet_ids": [
                "1619453502316740608"
            ],
            "created_at": "2023-01-28T21:52:57.000Z"
        },
        {
            "text": "@futebol_info Filha da puta pé-frio",
            "id": "1619453359811088386",
            "edit_history_tweet_ids": [
                "1619453359811088386"
            ],
            "created_at": "2023-01-28T21:52:23.000Z"
        },
        {
            "text": "É pé-frio que chama? https://t.co/u1S3LNb1Rf",
            "id": "1619452485890101249",
            "edit_history_tweet_ids": [
                "1619452485890101249"
            ],
            "created_at": "2023-01-28T21:48:55.000Z"
        },
        {
            "text": "Pé-Frio!!! 😡 https://t.co/gdKH34isj5",
            "id": "1619452017684144129",
            "edit_history_tweet_ids": [
                "1619452017684144129"
            ],
            "created_at": "2023-01-28T21:47:03.000Z"
        },
        {
            "text": "Acho que a primeira dama é pé-frio. Kkkkkk",
            "id": "1619451786586382337",
            "edit_history_tweet_ids": [
                "1619451786586382337"
            ],
            "created_at": "2023-01-28T21:46:08.000Z"
        },
        {
            "text": "O flamengo iria ganhar o jogo, mas Janja assombrosa pé-frio estragou tudo kkkkkkkkkkkkk",
            "id": "1619450786253262848",
            "edit_history_tweet_ids": [
                "1619450786253262848"
            ],
            "created_at": "2023-01-28T21:42:10.000Z"
        },
        {
            "text": "Além de brega, pé-frio.",
            "id": "1619450183485620225",
            "edit_history_tweet_ids": [
                "1619450183485620225"
            ],
            "created_at": "2023-01-28T21:39:46.000Z"
        },
        {
            "text": "Mais uma vitória sem o pé-frio do @bruno_zane . @ Estádio Municipal Do Pinhão https://t.co/RQMm281cpx",
            "id": "1619440330155216899",
            "edit_history_tweet_ids": [
                "1619440330155216899"
            ],
            "created_at": "2023-01-28T21:00:37.000Z"
        },
        {
            "text": "@Flamengo David Luiz vai completar a coleção de vices, pensa num zagueiro pé-frio. Tirar esse cara agora. Está fazendo o papel de cone hoje em campo. #VamosFlamengo #PALxFLA #SupercopaDoBrasil",
            "id": "1619431649342799872",
            "edit_history_tweet_ids": [
                "1619431649342799872"
            ],
            "created_at": "2023-01-28T20:26:07.000Z"
        },
        {
            "text": "David Luiz é uma tristeza sem fim. Dando condição no impedimento e depois assistência para o Rafael Veiga. Zagueiro pé-frio do caralhes. #VamosFlamengo #PALxFLA #SupercopaDoBrasil",
            "id": "1619429084681089025",
            "edit_history_tweet_ids": [
                "1619429084681089025"
            ],
            "created_at": "2023-01-28T20:15:55.000Z"
        },
        {
            "text": "Totoi não foi pro jogo e a irmã pé-frio do Gabi sim. O flamenguista não tem um dia de paz. rs #PALxFLA",
            "id": "1619381171754012673",
            "edit_history_tweet_ids": [
                "1619381171754012673"
            ],
            "created_at": "2023-01-28T17:05:32.000Z"
        },
        {
            "text": "POR FAVOR, vocês não inventem de levar amigo pé-frio amanhã pra Fonte Nova, sentar num setor diferente…",
            "id": "1619320359945383938",
            "edit_history_tweet_ids": [
                "1619320359945383938"
            ],
            "created_at": "2023-01-28T13:03:53.000Z"
        },
        {
            "text": "Parece milagre, o pé-frio do Twitter não funcionou dessa vez. \n#BBB23",
            "id": "1618790351531040775",
            "edit_history_tweet_ids": [
                "1618790351531040775"
            ],
            "created_at": "2023-01-27T01:57:50.000Z"
        },
        {
            "text": "Faltava mesmo uma mão-furada pra combinar com o pé-frio do Jovem Nerd.\nhttps://t.co/YxzWaMUvyL https://t.co/9OnyLGuMRU",
            "id": "1618720558899765249",
            "edit_history_tweet_ids": [
                "1618720558899765249"
            ],
            "created_at": "2023-01-26T21:20:30.000Z"
        },
        {
            "text": "Descobrimos o pé-frio telemático. https://t.co/AKp48xBXIf",
            "id": "1618331314750652416",
            "edit_history_tweet_ids": [
                "1618331314750652416"
            ],
            "created_at": "2023-01-25T19:33:47.000Z"
        },
        {
            "text": "Rapaz, parece que o Prefeitão é o maior pé-frio da política Amapaense de todos os tempos: apoiou o Jaime, sal; lançou a mulher, sal; e agora declarou apoio pro Kaká na ALAP e parece que lá o negócio deu ruim também. Tedoidé?",
            "id": "1618259185841614853",
            "edit_history_tweet_ids": [
                "1618259185841614853"
            ],
            "created_at": "2023-01-25T14:47:10.000Z"
        },
        {
            "text": "Pé-frio: homem investe R$ 40 mil na Americanas horas antes do rombo - Edital Concursos Brasil, https://t.co/hZWCrZxHfp",
            "id": "1617749390168363008",
            "edit_history_tweet_ids": [
                "1617749390168363008"
            ],
            "created_at": "2023-01-24T05:01:25.000Z"
        },
        {
            "text": "Pé-frio: homem investe R$ 40 mil na Americanas horas antes de o rombo vazar.....Leia mais em.... https://t.co/13DevUcRiO\nhttps://t.co/13DevUcRiO",
            "id": "1617722847237111809",
            "edit_history_tweet_ids": [
                "1617722847237111809"
            ],
            "created_at": "2023-01-24T03:15:57.000Z"
        },
        {
            "text": "Pé-frio: homem investe R$ 40 mil na Americanas horas antes de o rombo vazar https://t.co/dQdBLjyjKJ\nhttps://t.co/dQdBLjyjKJ",
            "id": "1617722845819469826",
            "edit_history_tweet_ids": [
                "1617722845819469826"
            ],
            "created_at": "2023-01-24T03:15:56.000Z"
        },
        {
            "text": "@LucasAlencarA11 @marcosbrazrio Esse Pé-Frio pisou o território do Mengão, numa semana de decisão?\nChama padre, o pai-de-santo, pastor...\nManda Benzer!",
            "id": "1617595484822175744",
            "edit_history_tweet_ids": [
                "1617595484822175744"
            ],
            "created_at": "2023-01-23T18:49:51.000Z"
        },
        {
            "text": "O pé-frio do Twitter é uma merda. \n#BBB23 https://t.co/WMF39fzdRw",
            "id": "1617362539494375424",
            "edit_history_tweet_ids": [
                "1617362539494375424"
            ],
            "created_at": "2023-01-23T03:24:13.000Z"
        },
        {
            "text": "Apenas pedindo para que o pé-frio dessa rede social dê uma trégua hoje... \n#BBB23",
            "id": "1617360223710203904",
            "edit_history_tweet_ids": [
                "1617360223710203904"
            ],
            "created_at": "2023-01-23T03:15:01.000Z"
        },
        {
            "text": "7. Pipico é gente boa, mas pé-frio demais\n8. Ressurreição linda do Maranhão, demolidor de cartazes\n9. Parnahyba e Sousa podem não ganhar, mas jogam campeonatos com uma puta imposição moral contra qualquer adversário\n10. A deserção no CSE é uma incógnita. Merece série na Netflix",
            "id": "1617315740432101377",
            "edit_history_tweet_ids": [
                "1617315740432101377"
            ],
            "created_at": "2023-01-23T00:18:15.000Z"
        },
        {
            "text": "Vergne é o maior pé-frio para companheiros de equipe https://t.co/SvpkjC6c3h",
            "id": "1616973000481316864",
            "edit_history_tweet_ids": [
                "1616973000481316864"
            ],
            "created_at": "2023-01-22T01:36:19.000Z"
        },
        {
            "text": "O meu chefe é colorado e tem fama de pé-frio.\n\nAdivinhem onde ele tá com toda a família?",
            "id": "1616933061144223744",
            "edit_history_tweet_ids": [
                "1616933061144223744"
            ],
            "created_at": "2023-01-21T22:57:37.000Z"
        },
        {
            "text": "@quemehcarol isso se chama-se autoconhecimento! o cara SABE que é pé-frio",
            "id": "1616920965635624962",
            "edit_history_tweet_ids": [
                "1616920965635624962"
            ],
            "created_at": "2023-01-21T22:09:33.000Z"
        },
        {
            "text": "@isadosilencio Mas vc é muito pé-frio mesmo! Nunca entrarei em bolão da megasena se vc estiver nele. KKKKKKKKKKKK",
            "id": "1616210507463008261",
            "edit_history_tweet_ids": [
                "1616210507463008261"
            ],
            "created_at": "2023-01-19T23:06:27.000Z"
        },
        {
            "text": "Para no quedar como un pelotudo, como te pasa siempre, averiguá que quiere decir pé-frio en protugués.\n\"Andá payá BOBOOOOOOOOO\" https://t.co/64l99jLFKx",
            "id": "1616173087401324544",
            "edit_history_tweet_ids": [
                "1616173087401324544"
            ],
            "created_at": "2023-01-19T20:37:45.000Z"
        },
        {
            "text": "@Oledobrasil pé-frio",
            "id": "1616133057777659905",
            "edit_history_tweet_ids": [
                "1616133057777659905"
            ],
            "created_at": "2023-01-19T17:58:41.000Z"
        },
        {
            "text": "A sina do tuiteiro pé-frio quando resolve shippar é essa mesmo https://t.co/XnkryBaXjw",
            "id": "1615975364051836928",
            "edit_history_tweet_ids": [
                "1615975364051836928"
            ],
            "created_at": "2023-01-19T07:32:04.000Z"
        },
        {
            "text": "Lula: \"Servidores públicos federais não recebem aumento há 7 anos\".\n\nEntrei na Ufam justamente há 7,5 anos.\nSou pé-frio mesmo.",
            "id": "1615866954719563776",
            "edit_history_tweet_ids": [
                "1615866954719563776"
            ],
            "created_at": "2023-01-19T00:21:18.000Z"
        },
        {
            "text": "@mspbra @edishi62 Que pé-frio em Zoe.",
            "id": "1615769570110750732",
            "edit_history_tweet_ids": [
                "1615769570110750732"
            ],
            "created_at": "2023-01-18T17:54:19.000Z"
        },
        {
            "text": "O tuiteiro é um bicho azarado… Anos de tombo, de pé-frio, mas a gente não aprende",
            "id": "1615745103020032006",
            "edit_history_tweet_ids": [
                "1615745103020032006"
            ],
            "created_at": "2023-01-18T16:17:06.000Z"
        },
        {
            "text": "@LucasBuenoA Se existissem redes sociais na década de 80, Cilinho seria Prof. Pardal e Telê seria contestado na contratação, por ser \"pé-frio\".",
            "id": "1615063468293632002",
            "edit_history_tweet_ids": [
                "1615063468293632002"
            ],
            "created_at": "2023-01-16T19:08:31.000Z"
        },
        {
            "text": "[15/1 17:34] maggot: Onde eu assisto futebol pela net?\n[15/1 17:35] pupas: Futemax\n[15/1 17:38] Marcos Rian: meu Deus maggot\n[15/1 17:38] Marcos Rian: fecha isso antes que seja tarde\n[15/1 17:39] maggot: Eu n costumo ser pé-frio n, ta de boa\n\ngol do bragantino",
            "id": "1614724520731885568",
            "edit_history_tweet_ids": [
                "1614724520731885568"
            ],
            "created_at": "2023-01-15T20:41:40.000Z"
        },
        {
            "text": "clube mais pé-frio que há, que sina",
            "id": "1614714733185081346",
            "edit_history_tweet_ids": [
                "1614714733185081346"
            ],
            "created_at": "2023-01-15T20:02:46.000Z"
        },
        {
            "text": "@PaparazzoRN @Casimiro Que bom! Casemiro é pé-frio! Viu o que deu na Copa?",
            "id": "1614420463056289794",
            "edit_history_tweet_ids": [
                "1614420463056289794"
            ],
            "created_at": "2023-01-15T00:33:27.000Z"
        },
        {
            "text": "Pé-frio esse aí. Só ver na copa! https://t.co/xs1n1qWUnb",
            "id": "1614397028255113216",
            "edit_history_tweet_ids": [
                "1614397028255113216"
            ],
            "created_at": "2023-01-14T23:00:20.000Z"
        },
        {
            "text": "@_matheusfla Pé-frio esse aí. Só ver na copa!",
            "id": "1614396994776096768",
            "edit_history_tweet_ids": [
                "1614396994776096768"
            ],
            "created_at": "2023-01-14T23:00:12.000Z"
        },
        {
            "text": "Parabéns Real Madrid pela taça. Cazé é pé-frio https://t.co/XMa65pchmT",
            "id": "1614049137548472320",
            "edit_history_tweet_ids": [
                "1614049137548472320"
            ],
            "created_at": "2023-01-13T23:57:56.000Z"
        },
        {
            "text": "@Casimiro Cazé é pé-frio",
            "id": "1614049032023711753",
            "edit_history_tweet_ids": [
                "1614049032023711753"
            ],
            "created_at": "2023-01-13T23:57:31.000Z"
        },
        {
            "text": "Obrigado Suga pé-frio",
            "id": "1613982139694858240",
            "edit_history_tweet_ids": [
                "1613982139694858240"
            ],
            "created_at": "2023-01-13T19:31:43.000Z"
        },
        {
            "text": "@Carol__Freitas @papodebola ainda bem que o Edu também é pé-frio. 🙏",
            "id": "1613748927227904000",
            "edit_history_tweet_ids": [
                "1613748927227904000"
            ],
            "created_at": "2023-01-13T04:05:00.000Z"
        },
        {
            "text": "🤣🤣🤣🤣🤣 faz sentido, o cara é o pé-frio das copas… https://t.co/BTyOBZvgsJ",
            "id": "1613646941400842240",
            "edit_history_tweet_ids": [
                "1613646941400842240"
            ],
            "created_at": "2023-01-12T21:19:45.000Z"
        },
        {
            "geo": {
                "place_id": "0090a6f53f20ebd0"
            },
            "text": "incrível como é pé-frio o rapaz https://t.co/gVmg980nKr",
            "id": "1613309236171407360",
            "edit_history_tweet_ids": [
                "1613309236171407360"
            ],
            "created_at": "2023-01-11T22:57:50.000Z"
        },
        {
            "text": "@JefRodriguezz @swiftgostosona @querolitio Deixa ela dormir, cuzão, ela é pé-frio",
            "id": "1612997507906244608",
            "edit_history_tweet_ids": [
                "1612997507906244608"
            ],
            "created_at": "2023-01-11T02:19:08.000Z"
        },
        {
            "text": "@futnostalgico @Flamengo Olympikus. A Umbro foi meio pé-frio em sua passagem e a Nike, apesar de alguns belos uniformes, foi uma bagunça.",
            "id": "1612659376573095936",
            "edit_history_tweet_ids": [
                "1612659376573095936"
            ],
            "created_at": "2023-01-10T03:55:31.000Z"
        },
        {
            "text": "“As crianças chegaram-se para mais perto de Brejeiro, uma de cada lado: tinham dito lá em cima que se tratava de um pé-frio, mas ali embaixo ele era o seu único conforto.”\n\ncap. X; pag. 130",
            "id": "1612597062347923456",
            "edit_history_tweet_ids": [
                "1612597062347923456"
            ],
            "created_at": "2023-01-09T23:47:54.000Z"
        },
        {
            "text": "Sigo sendo a pessoa mais pé-frio do mundo\n\nAtlético de Madrid X Barcelona https://t.co/qE49V3e6Hi",
            "id": "1612239734029287424",
            "edit_history_tweet_ids": [
                "1612239734029287424"
            ],
            "created_at": "2023-01-09T00:08:01.000Z"
        }
    ]

init()
