import nest_asyncio
nest_asyncio.apply()

import asyncio
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import requests
from bs4 import BeautifulSoup
import g4f
from telegram import Bot, InputMediaPhoto

def get_news():
    url = "https://stopgame.ru/news"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    news_cards = soup.find_all('div', class_='_card_1vlem_1')
    
    news_list = []
    
    for card in news_cards[:5]:  # Обрабатываем только первые 5 новостей
        title = card.find('a', class_='_title_1vlem_60').text.strip()
        link = "https://stopgame.ru" + card.find('a', class_='_title_1vlem_60')['href']
        
        image_tag = card.find('img', class_='_image_1vlem_20 img') or card.find('img')
        image = image_tag['src'] if image_tag else "Изображение не найдено"
        
        news_content = get_news_content(link)
        
        # Перефразируем заголовок и содержание
        rephrased_title, rephrased_content = rephrase_for_telegram(title, news_content)
        
        news_list.append({
            'title': rephrased_title,
            'link': link,
            'image': image,
            'content': rephrased_content
        })
    
    return news_list

def get_news_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    content = ""
    paragraphs = soup.find_all('p', class_='_text_12po9_111')
    quotes = soup.find_all('blockquote')
    
    for p in paragraphs:
        content += p.text.strip() + "\n\n"
    
    for q in quotes:
        content += "Цитата: " + q.text.strip() + "\n\n"
    
    return content.strip()

def rephrase_for_telegram(title, content):
    prompt = f"""Перефразируй следующий заголовок и содержание новости в формат телеграм-поста. 
    Сделай текст более кратким и привлекательным для читателей.
    
    Заголовок: {title}
    
    Содержание:
    {content}
    
    Пожалуйста, верни результат в формате:
    Заголовок: <перефразированный заголовок>
    Содержание: <перефразированное содержание>
    """
    
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    
    # Разделяем ответ на заголовок и содержание
    lines = response.split('\n')
    rephrased_title = lines[0].replace('Заголовок: ', '').strip()
    rephrased_content = '\n'.join(lines[2:]).replace('Содержание: ', '').strip()
    
    return rephrased_title, rephrased_content

async def send_to_telegram(bot, chat_id, news):
    for item in news:
        caption = f"*{item['title']}*\n\n{item['content']}\n\n[Подробнее]({item['link']})\n\n"
        caption += "Больше статей и обзоров можно приобрести у автора Максим Кузьмин на бирже текстов Адвего: https://advego.com/shop/find/?so=1&a=MaksimKuzmin3"
        
        try:
            await bot.send_photo(chat_id=chat_id, photo=item['image'], caption=caption, parse_mode='Markdown')
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            # Попробуем отправить без изображения, если возникла ошибка
            try:
                await bot.send_message(chat_id=chat_id, text=caption, parse_mode='Markdown')
            except Exception as e:
                print(f"Ошибка при отправке текстового сообщения: {e}")

def display_and_select_news(news):
    print("Доступные новости:")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
    
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
    BOT_TOKEN = BOT_TOKEN
    CHAT_ID = CHAT_ID    
    bot = Bot(token=BOT_TOKEN)
    news = get_news()
    
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

import subprocess
import sys

def update_libraries():
    libraries = [
        'Flask', 'httpx', 'beautifulsoup4', 'g4f', 'python-telegram-bot', 
        'nest_asyncio', 'requests', 'httpcore', 'anyio'
    ]
    for lib in libraries:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", lib])

if __name__ == "__main__":
    update_libraries()
    asyncio.run(main())
   