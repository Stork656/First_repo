FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# **Добавляем скачивание NLTK-данных**
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='SkolkovoInstitute/russian_toxicity_classifier')"


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

