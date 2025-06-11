import tensorflow as tf
from preprocessing import preprocess_text, tokenize_and_pad 

#Загрузка модели
model = tf.keras.models.load_model("model.h5")

#Функция предсказания
def predict_spam(text):
    processed_text = preprocess_text(text)  #Очистка, удаление стоп-слов, лемматизация
    tokenized_text = tokenize_and_pad([processed_text])  #Токенизация и паддинг
    prediction = model.predict(tokenized_text)  #Получаем предсказание

    return "spam" if prediction[0][0] > 0.5 else "not spam"

