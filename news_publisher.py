import nest_asyncio
nest_asyncio.apply()

import asyncio
import sys
import httpx
from bs4 import BeautifulSoup
import g4f
from telegram import Bot
from datetime import datetime, time

async def get_news():
    categories = [
        "https://stopgame.ru/news",
        "https://stopgame.ru/news/mobile",
        "https://stopgame.ru/news/cybersport"
    ]
    news_list = []

    async with httpx.AsyncClient() as client:
        for url in categories:
            response = await client.get(url)
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            news_cards = soup.find('div', class_='_section-with-pagination_1jnog_1118').find_all('div', class_='_card_1vlem_1')

            for card in news_cards[:2]:
                title = card.find('a', class_='_title_1vlem_60').text.strip()
                if not title:  # Пропускаем пустые заголовки
                    continue
                link = "https://stopgame.ru" + card.find('a', class_='_title_1vlem_60')['href']
                image_tag = card.find('img', class_='_image_1vlem_20 img') or card.find('img')
                image = image_tag['src'] if image_tag else "Изображение не найдено"
                news_content = await get_news_content(link)
                rephrased_title, rephrased_content, hashtags = rephrase_for_telegram(title, news_content['content'])

                news_list.append({
                    'title': rephrased_title,
                    'link': link,
                    'image': image,
                    'content': rephrased_content,
                    'hashtags': hashtags
                })

    return news_list

async def get_news_content(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        content = response.text

    soup = BeautifulSoup(content, 'html.parser')
    video = soup.find('div', class_='_video-wrapper_12po9_397') or soup.find('div', class_='lite-youtube')

    if video:
        video_url = video.get('data-src') or video.get('data-yt-id')
        if video_url:
            if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
                video_url = f"https://www.youtube.com/watch?v={video_url}"
            return {'type': 'video', 'url': video_url}

    content = ""
    paragraphs = soup.find_all('p', class_='_text_12po9_111')
    quotes = soup.find_all('blockquote')

    for p in paragraphs:
        content += p.text.strip() + "\n\n"

    for q in quotes:
        content += "Цитата: " + q.text.strip() + "\n\n"

    return {'type': 'text', 'content': content.strip()}

def rephrase_for_telegram(title, content):
    prompt = f"""Перефразируй следующий заголовок и содержание новости в формат телеграм-поста. 
    Сделай текст более кратким и привлекательным для читателей.

    Заголовок: {title}

    Содержание:
    {content}

    Пожалуйста, верни результат в формате:
    Заголовок: <перефразированный заголовок>
    Содержание: <перефразированное содержание>
    Хештеги: <сгенерированные хештеги через запятую>
    """

    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )

    lines = response.split('\n')
    rephrased_title = lines[0].replace('Заголовок: ', '').strip()
    rephrased_content = '\n'.join(lines[2:]).replace('Содержание: ', '').strip()
    hashtags = lines[-1].replace('Хештеги: ', '').strip().split(',')

    return rephrased_title, rephrased_content, hashtags

async def send_to_telegram(bot, chat_id, news):
    for item in news:
        if isinstance(item['content'], dict) and item['content']['type'] == 'video':
            caption = f"*{item['title']}*\n\nВидео взято с сайта https://stopgame.ru"
            await bot.send_video(chat_id=chat_id, video=item['content']['url'], caption=caption, parse_mode='Markdown')
        else:
            caption = f"*{item['title']}*\n\n{item['content']}\n\n[Подробнее]({item['link']})\n\n"
            caption += "Больше статей и обзоров можно приобрести у автора Максим Кузьмин на бирже текстов Адвего: https://advego.com/shop/find/?so=1&a=MaksimKuzmin3"
        
        hashtags = ", ".join(item['hashtags'])
        caption += f"\n\n{hashtags}"
        
        await bot.send_photo(chat_id=chat_id, photo=item['image'], caption=caption, parse_mode='Markdown')

async def publish_news():
    bot_token = '7027432337:AAFL2bQ59f7mcF_W1MxrP50TW8GeL-nv9OQ'
    chat_id = '-1002171314359'
    bot = Bot(token=bot_token)

    news_count = 0  # Счетчик опубликованных новостей
    start_time = datetime.now()  # Запоминаем время начала

    while True:
        now = datetime.now()
        elapsed_time = (now - start_time).seconds  # Время, прошедшее с начала

        if elapsed_time >= 3600:  # Если прошло 1 час
            break  # Выходим из цикла

        if news_count < 2:  # Публикуем не более 2 новостей
            news = await get_news()
            if news:
                await send_to_telegram(bot, chat_id, news)
                news_count += 1  # Увеличиваем счетчик новостей
            await asyncio.sleep(60)  # Ждем 1 минуту перед следующей публикацией
        else:
            await asyncio.sleep(1)  # Проверяем каждую секунду

if __name__ == "__main__":
    asyncio.run(publish_news())