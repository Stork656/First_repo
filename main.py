from fastapi import FastAPI
from pydantic import BaseModel
from predict import predict_spam

#Создаём API
app = FastAPI()

#Определяем модель запроса
class EmailRequest(BaseModel):
    text: str

#Эндпоинт для предсказания
@app.post("/predict")
def classify_email(request: EmailRequest):
    result = predict_spam(request.text)
    return {"prediction": result}

#Тестовый эндпоинт
@app.get("/")
def home():
    return {"message": "API запущен"}

#Запуск сервера (локально)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
