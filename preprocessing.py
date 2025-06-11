import re
import nltk
import pickle
import pymorphy2
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from transformers import pipeline


def download_nltk_data():
    """Загрузка данных NLTK"""
    for resource in ['wordnet', 'stopwords', 'omw-1.4']:
        try:
            nltk.data.find(f'corpora/{resource}')
        except LookupError:
            nltk.download(resource)

download_nltk_data()

#Инициализация инструментов
morph = pymorphy2.MorphAnalyzer()
lemmatizer = WordNetLemmatizer()
classifier = pipeline('text-classification', model = 'SkolkovoInstitute/russian_toxicity_classifier')

#Токенизатор
with open("tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

def clean_text(text):
    """Очистка от лишних символов"""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)  #Удаление HTML-тегов
    text = re.sub(r'\n', ' ', text)  #Удаление переносов строк
    text = re.sub(r'[^a-zа-яё\s]', '', text)  #Удаление пунктуации и символов
    return text

def remove_stopwords(text):
    """Удаляение стоп-слов"""
    stop_words_eng = set(stopwords.words('english'))
    stop_words_rus = set(stopwords.words('russian'))
    stop_words = stop_words_eng.union(stop_words_rus)
    words = [word for word in text.split() if word not in stop_words]
    return ' '.join(words)

def lemmatize_text(text):
    """Лемматизация."""
    lemmatized_words = []
    for word in text.split():
        if any('а' <= char <= 'я' for char in word):
            lemmatized_words.append(morph.parse(word)[0].normal_form)
        elif any('a' <= char <= 'z' for char in word):
            lemmatized_words.append(lemmatizer.lemmatize(word))
        else:
            lemmatized_words.append(word)
    return ' '.join(lemmatized_words)

def preprocess_text(text):
    """Предобработка текста"""
    text = clean_text(text)
    text = remove_stopwords(text)
    text = lemmatize_text(text)
    return text

def tonality(text):
    """Функция определения тональности"""
    result = classifier(text[:512])  # Ограничиваем до 512 символов
    if result:
        return result[0]['label']
    return ''

def tokenize_and_pad(texts, max_len=150):
    """Токенизация и формирование последовательностей"""
    sequences = tokenizer.texts_to_sequences(texts)
    padded = pad_sequences(sequences, maxlen=max_len)
    return padded
