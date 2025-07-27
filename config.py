# config.py - Enhanced with international AI news sources
import os
from dotenv import load_dotenv

load_dotenv()

# International AI News Sources (English)
NEWS_SOURCES = {
    "tech_general": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "https://venturebeat.com/ai/feed/",
        "https://www.wired.com/category/artificial-intelligence/feed/",
        "https://singularityhub.com/feed/",
        "https://machinelearningmastery.com/feed/",
        "https://towardsdatascience.com/feed",
        "https://www.artificialintelligence-news.com/feed/",
    ],
    "ai_research": [
        "https://deepmind.com/blog/rss.xml",
        "https://openai.com/blog/rss.xml",
        "https://blogs.nvidia.com/feed/",
        "https://ai.googleblog.com/feeds/posts/default",
        "https://www.microsoft.com/en-us/research/feed/",
    ],
    "ai_industry": [
        "https://www.artificialintelligence-news.com/feed/",
        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
        "https://www.forbes.com/ai/feed/",
        "https://spectrum.ieee.org/rss/topic/artificial-intelligence",
    ],
    "ai_academic": [
        "https://distill.pub/rss.xml",
        "https://arxiv.org/rss/cs.AI",
        "https://arxiv.org/rss/cs.LG",  # Machine Learning
        "https://arxiv.org/rss/cs.CL",  # Computational Linguistics
    ],
    "中文AI源": [
        "https://www.jiqizhixin.com/rss",
        "https://36kr.com/feed",
        "https://www.leiphone.com/feed"
    ]
}

# Database configuration
DATABASE_CONFIG = {
    'path': 'ai_news.db',
    'backup_days': 30
}

# LLM Configuration
LLM_CONFIG = {
    'model_name': 'llama3.1:8b',
    'base_url': 'http://localhost:11434',
    'temperature': 0.7,
    'max_tokens': 1000
}

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('EMAIL_SMTP_SERVER'),
    'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', 587)),
    'email': os.getenv('EMAIL_ADDRESS'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'to_email': os.getenv('EMAIL_TO')
}

# Obsidian Configuration
OBSIDIAN_CONFIG = {
    'vault_path': os.getenv('OBSIDIAN_VAULT_PATH'),
    'notes_folder': os.getenv('OBSIDIAN_NOTES_FOLDER', 'AI_News'),
    'daily_notes': True,
    'individual_notes': True
}

# Streamlit UI Configuration
UI_CONFIG = {
    'page_title': 'AI News Aggregator',
    'page_icon': '🤖',
    'layout': 'wide',
    'theme': 'dark'
}