import nest_asyncio
nest_asyncio.apply()

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import aiohttp
from bs4 import BeautifulSoup
import g4f
from telegram import Bot, InputMediaPhoto
async def get_news():
    url = "https://stopgame.ru/news"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()

    soup = BeautifulSoup(content, 'html.parser')
    news_cards = soup.find_all('div', class_='_card_1vlem_1')

    news_list = []
    tasks = []

    for card in news_cards[:5]:
        original_title = card.find('a', class_='_title_1vlem_60').text.strip()
        link = "https://stopgame.ru" + card.find('a', class_='_title_1vlem_60')['href']
    
        image_tag = card.find('img', class_='_image_1vlem_20 img') or card.find('img')
        image = image_tag['src'] if image_tag else "Изображение не найдено"
    
        tasks.append(asyncio.create_task(process_news(original_title, link, image)))

    news_list = await asyncio.gather(*tasks)
    return news_list

async def process_news(original_title, link, image):
    news_content = await get_news_content(link)
    return {
        'original_title': original_title,
        'link': link,
        'image': image,
        'content': news_content
    }

async def get_news_content(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()

    soup = BeautifulSoup(content, 'html.parser')

    paragraphs = soup.find_all('p', class_='_text_12po9_111')
    quotes = soup.find_all('blockquote')

    content = "\n\n".join([p.text.strip() for p in paragraphs])
    content += "\n\n" + "\n\n".join([f"Цитата: {q.text.strip()}" for q in quotes])

    return content.strip()

async def send_to_telegram(bot, chat_id, news):
    tasks = []
    for item in news:
        caption = f"✨ *{item['original_title']}*\n\n"
        caption += f"📰 {item['content']}\n\n"
        caption += f"[Подробнее]({item['link']})\n\n"
        caption += "🔗 Больше статей и обзоров можно приобрести у автора Максим Кузьмин на бирже текстов Адвего: https://advego.com/shop/find/?so=1&a=MaksimKuzmin3"
        
        caption += "\n\n---\n\n"  # Разделитель между новостями
        
        tasks.append(send_single_news(bot, chat_id, item['image'], caption))
    
    await asyncio.gather(*tasks)

async def send_single_news(bot, chat_id, image, caption):
    try:
        await bot.send_photo(chat_id=chat_id, photo=image, caption=caption, parse_mode='Markdown')
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        try:
            await bot.send_message(chat_id=chat_id, text=caption, parse_mode='Markdown')
        except Exception as e:
            print(f"Ошибка при отправке текстового сообщения: {e}")

def display_and_select_news(news):
    print("Доступные новости:")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['original_title']}")
    
    while True:
        try:
            choice = int(input(f"Выберите номер новости для публикации (1-{len(news)}): "))
            if 1 <= choice <= len(news):
                return [news[choice - 1]]
            else:
                print(f"Пожалуйста, выберите число от 1 до {len(news)}.")
        except ValueError:
            print("Пожалуйста, введите корректное число.")

async def main():
    from config import BOT_TOKEN, CHAT_ID
    bot = Bot(token=BOT_TOKEN)
    news = await get_news()
    
    if not news:
        print("Не удалось получить новости. Проверьте подключение к интернету или доступность сайта.")
        return
    
    selected_news = display_and_select_news(news)
    
    await send_to_telegram(bot, CHAT_ID, selected_news)
    print("Выбранная новость успешно отправлена в Telegram")

import logging

"""
Этот скрипт получает новости с сайта stopgame.ru, перефразирует их с помощью GPT
и отправляет в Telegram канал. Пользователь может выбрать одну новость для публикации.
"""

if __name__ == "__main__":
    asyncio.run(main())
