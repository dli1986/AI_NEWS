import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sqlite3
from dataclasses import dataclass
from typing import List

@dataclass
class NewsItem:
    title: str
    url: str
    summary: str
    published_date: datetime
    source: str
    content: str = ""
    ai_summary: str = ""

class NewsCollector:
    def __init__(self, db_path: str = "ai_news.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                summary TEXT,
                published_date TEXT,
                source TEXT,
                content TEXT,
                ai_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def collect_rss_news(self, rss_urls: List[str]) -> List[NewsItem]:
        """采集RSS新闻"""
        news_items = []
        yesterday = datetime.now() - timedelta(days=1)
        
        for url in rss_urls:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get('title', 'Unknown')
                
                for entry in feed.entries:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date >= yesterday:
                        news_item = NewsItem(
                            title=entry.title,
                            url=entry.link,
                            summary=entry.get('summary', ''),
                            published_date=pub_date,
                            source=source_name
                        )
                        news_items.append(news_item)
            except Exception as e:
                print(f"Error collecting from {url}: {e}")
        
        return news_items
    
    def extract_full_content(self, url: str) -> str:
        """提取文章完整内容"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本和样式元素
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取主要内容
            content = soup.get_text()
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
            
            return content[:5000]  # 限制内容长度
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return ""