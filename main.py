import requests
import colorama
import datetime
import time
import nltk
import numpy
from bs4 import BeautifulSoup
from itertools import cycle
from collections import defaultdict
from colorama import Fore
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer 
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('punkt')
nltk.download('stopwords')
colorama.init(autoreset=True)
try:
    with open('proxies.txt', 'r+', encoding='utf-8') as f:
        proxypool = cycle(f.read().splitlines()) #prevents ratelimits
except:
    pass

def getNetwork(URL):
    time.sleep(1)
    res = requests.get(URL).text
    soup = BeautifulSoup(res, 'lxml')
    try:
        price = soup.find('div', {'class':'YMlKec fxKbKc'}).text
    except AttributeError:
        price = None
    return soup, price

class Polling:
    def __init__(self, symbols, exchange = 'nasdaq'):
        self.symbols = [symbol.strip(' ') for symbol in symbols.split(',')]
        self.tickers = [f'https://www.google.com/finance/quote/{symbol}:{exchange}?hl=en' for symbol in self.symbols] 
        self.sources = defaultdict(list)

    def poll(self):
        for URL in self.tickers:
            soup, price = getNetwork(URL)
            ticker = URL.split('/')[5].split(':')[0]
            stock_quotes = soup.find_all('div', {'class':'yY3Lee'})
            if (previous_price := soup.find('div', {'class':'P6K39c'}).text) > price:
                print(f'{Fore.BLUE}{datetime.datetime.now()} {Fore.RED}{ticker} {Fore.GREEN}{previous_price} -----> {Fore.RED}{price}')
            else:
                print(f'{Fore.BLUE}{datetime.datetime.now()} {Fore.GREEN}{ticker} {Fore.RED}{previous_price} -----> {Fore.GREEN}{price}')
            for quote in stock_quotes:
                try:
                    relevancy = quote.find('div', {'class':'Yfwt5'}).text
                    caption = quote.find('div', {'class':'Adak'}).text
                    source = quote.find('div', {'class':'sfyJob'}).text
                    source_link = quote.find('a').get('href')
                except AttributeError:
                    print('AttributeError: NoneType object has no attribute text')
                else:
                    self.sources[f'{ticker}'].append(source_link)
                    print(f'{caption}:{source}:{relevancy}\n{source_link}')

    def analyze(self, n=5): 
        stop_words = set(stopwords.words('english'))
        tfidf = TfidfVectorizer(stop_words=['the', 'how', 'us', 'may', 'about', 'my', 'also', 'our', 'get', 'by', 'all', 'motley', 'fool', 'really', '2023', '2022', 'said', 'still', 'could', 'it', 'msft', 'microsoft'])
        #stemmer = PorterStemmer()
        for symbol in self.symbols:
            for source in self.sources[symbol]:
                corpus = ''
                soup, _ = getNetwork(source)
                main_text = soup.find('body').text
                corpus += main_text
            tokens = nltk.word_tokenize(corpus)
            filtered_tokens = [token for token in tokens if token not in stop_words]
            #stemmed_tokens = [stemmer.stem(token) for token in filtered_tokens]
            tfidf_matrix = tfidf.fit_transform(filtered_tokens)
            feature_names = tfidf.get_feature_names_out()
            tfidf_scores = zip(feature_names, numpy.asarray(tfidf_matrix.sum(axis=0)).ravel())
            sorted_scores = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
            important_keywords = [s[0] for s in sorted_scores[:n]]
            print(important_keywords)

    def extract_important_sentences(self, n=2):
        tfidf = TfidfVectorizer()
        for symbol in self.symbols:
            for source in self.sources[symbol]:
                corpus = ''
                soup, _ = getNetwork(source)
                main_text = soup.find('body').text
                corpus += main_text
            sentences = nltk.sent_tokenize(main_text)
            tfidf_matrix = tfidf.fit_transform(sentences)
            #sorted_index = (-tfidf_matrix.sum(axis=0)).argsort().A1[-10:].tolist()
            sorted_index = numpy.argsort(-tfidf_matrix.toarray(), axis=0)[:n]
            important_sentences = [sentences[i] for i in sorted_index.flatten()[:n]]
            print(important_sentences)

def run():
    while True:
        tickers = input('enter stock tickers like tlry, aapl, msft \n')
        if len(tickers) == 0:
            break
        user = Polling(tickers)
        try:
            user.poll()
        except Exception:
            print('ticker(s) could not be found')
        finally:
            try:
                user.analyze()
                user.extract_important_sentences() 
            except Exception:
                print('important keywords and sentences could not be found')
        continue


run()
