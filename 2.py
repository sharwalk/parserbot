import asyncio
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import requests
from bs4 import BeautifulSoup
import g4f

def get_news():
    url = "https://stopgame.ru/news"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    news_cards = soup.find_all('div', class_='_section-with-pagination_1jnog_1118')
    
    news_list = []
    
    for card in news_cards:
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

def print_news(news_list):
    for news in news_list:
        print(f"Заголовок: {news['title']}")
        print(f"Ссылка: {news['link']}")
        print(f"Изображение: {news['image']}")
        print("Содержание:")
        print(news['content'])
        print("-" * 50)

if __name__ == "__main__":
    news = get_news()
    print_news(news)
    print("Новости успешно выведены в консоль")