from flask import Flask
import asyncio
import nest_asyncio
from news_publisher import publish_news  # Импортируем функцию для публикации новостей

app = Flask(__name__)

@app.route('/')
def home():
    return "Я жив"

async def run_news_publisher():
    await publish_news()

if __name__ == "__main__":
    nest_asyncio.apply()  # Применяем nest_asyncio для поддержки asyncio в Flask
    loop = asyncio.get_event_loop()
    loop.create_task(run_news_publisher())  # Запускаем публикацию новостей
    app.run(host='0.0.0.0', port=5000)