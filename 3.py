import nest_asyncio
nest_asyncio.apply()

import asyncio
import sys
import httpx

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from bs4 import BeautifulSoup
import g4f
from telegram import Bot, InputMediaPhoto

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
            
            for card in news_cards[:2]:  # Берем только первые 2 новости из каждой категории
                title = card.find('a', class_='_title_1vlem_60').text.strip()
                link = "https://stopgame.ru" + card.find('a', class_='_title_1vlem_60')['href']
                
                image_tag = card.find('img', class_='_image_1vlem_20 img') or card.find('img')
                image = image_tag['src'] if image_tag else "Изображение не найдено"
                
                news_content = await get_news_content(link)
                
                # Перефразируем заголовок и содержание, а также генерируем хештеги
                rephrased_title, rephrased_content, hashtags = rephrase_for_telegram(title, news_content['content'])
                
                news_list.append({
                    'title': rephrased_title,
                    'link': link,
                    'image': image,
                    'content': rephrased_content,
                    'hashtags': hashtags  # Сохраняем сгенерированные хештеги
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
    
    # Разделяем ответ на заголовок, содержание и хештеги
    lines = response.split('\n')
    rephrased_title = lines[0].replace('Заголовок: ', '').strip()
    rephrased_content = '\n'.join(lines[2:]).replace('Содержание: ', '').strip()
    hashtags = lines[-1].replace('Хештеги: ', '').strip().split(',')  # Получаем хештеги
    
    return rephrased_title, rephrased_content, hashtags

async def send_to_telegram(bot, chat_id, news):
    for item in news:
        if isinstance(item['content'], dict) and item['content']['type'] == 'video':
            caption = f"*{item['title']}*\n\nВидео взято с сайта https://stopgame.ru"
            message = await bot.send_video(chat_id=chat_id, video=item['content']['url'], caption=caption, parse_mode='Markdown')
        else:
            caption = f"*{item['title']}*\n\n{item['content']}\n\n[Подробнее]({item['link']})\n\n"
            caption += "Больше статей и обзоров можно приобрести у автора Максим Кузьмин на бирже текстов Адвего: https://advego.com/shop/find/?so=1&a=MaksimKuzmin3"
        
        # Добавляем хештеги
        hashtags = ", ".join(item['hashtags'])  # Преобразуем список хештегов в строку
        caption += f"\n\n{hashtags}"
        
        message = await bot.send_photo(chat_id=chat_id, photo=item['image'], caption=caption, parse_mode='Markdown')

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
    bot_token = '7027432337:AAFL2bQ59f7mcF_W1MxrP50TW8GeL-nv9OQ'
    chat_id = '-1002171314359'  # реальный ID
    
    bot = Bot(token=bot_token)
    
    try:
        news = await get_news()
        
        selected_news = display_and_select_news(news)
        
        await send_to_telegram(bot, chat_id, selected_news)
        print("Выбранная новость успешно отправлена в Telegram")
        
        # Добавляем небольшую задержку перед завершением
        await asyncio.sleep(1)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await bot.close()  # Закрываем бота только после завершения всех операций

if __name__ == "__main__":
    asyncio.run(main())