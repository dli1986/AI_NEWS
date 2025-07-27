# enhanced_output_dispatcher.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import markdown
from typing import List
from news_collector import NewsItem

class EnhancedOutputDispatcher:
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', 587)),
            'email': os.getenv('EMAIL_ADDRESS'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'to_email': os.getenv('EMAIL_TO')
        }
        
        self.obsidian_config = {
            'vault_path': os.getenv('OBSIDIAN_VAULT_PATH'),
            'notes_folder': os.getenv('OBSIDIAN_NOTES_FOLDER', 'AI_News'),
            'individual_notes_folder': os.getenv('OBSIDIAN_INDIVIDUAL_FOLDER', 'AI_News/Individual'),
            'daily_digest_folder': os.getenv('OBSIDIAN_DIGEST_FOLDER', 'AI_News/Daily_Digests')
        }

    def send_email(self, subject: str, content: str, is_html: bool = False):
        """Send email with enhanced formatting"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['email']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = subject
            
            # Convert markdown to HTML if needed
            if not is_html and '##' in content:
                html_content = markdown.markdown(content)
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            else:
                content_type = 'html' if is_html else 'plain'
                msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully: {subject}")
            return True
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False

    def save_individual_news_to_obsidian(self, news_items: List[NewsItem], date: str):
        """Save individual news items to separate Obsidian notes"""
        try:
            vault_path = Path(self.obsidian_config['vault_path'])
            individual_folder = vault_path / self.obsidian_config['individual_notes_folder']
            individual_folder.mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            for item in news_items:
                if item.ai_summary:  # Only save items with AI summaries
                    # Create safe filename
                    safe_title = "".join(c for c in item.title[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"{date}_{safe_title}.md"
                    file_path = individual_folder / filename
                    
                    # Create individual note content
                    note_content = self.create_individual_note_content(item, date)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(note_content)
                    
                    saved_count += 1
            
            print(f"✅ Saved {saved_count} individual notes to Obsidian")
            return saved_count
        except Exception as e:
            print(f"❌ Failed to save individual notes: {e}")
            return 0

    def save_daily_digest_to_obsidian(self, digest_content: str, date: str):
        """Save daily digest to Obsidian"""
        try:
            vault_path = Path(self.obsidian_config['vault_path'])
            digest_folder = vault_path / self.obsidian_config['daily_digest_folder']
            digest_folder.mkdir(parents=True, exist_ok=True)
            
            filename = f"AI_News_Digest_{date}.md"
            file_path = digest_folder / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(digest_content)
            
            print(f"✅ : {file_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save digest: {e}")
            return False

    def create_individual_note_content(self, item: NewsItem, date: str) -> str:
        """Create content for individual news note"""
        tags = self.extract_tags_from_summary(item.ai_summary)
        
        content = f"""---
title: "{item.title}"
date: {date}
source: "{item.source}"
url: "{item.url}"
published: {item.published_date.strftime('%Y-%m-%d %H:%M')}
tags: [{', '.join(tags)}]
---

# {item.title}

**Source**: {item.source}  
**Published**: {item.published_date.strftime('%Y-%m-%d %H:%M')}  
**URL**: [{item.url}]({item.url})

## AI Summary

{item.ai_summary}

## Original Summary

{item.summary}

## Links and References

- Original Article: [{item.title}]({item.url})
- Source: {item.source}

---
*Note created on {datetime.now().strftime('%Y-%m-%d %H:%M')} by AI News Aggregator*
"""
        return content

    def create_comprehensive_digest(self, news_items: List[NewsItem], date: str) -> str:
        """Create a comprehensive daily digest"""
        processed_items = [item for item in news_items if item.ai_summary]
        
        if not processed_items:
            return f"# AI News Digest - {date}\n\nNo news items processed today."
        
        # Group by source
        by_source = {}
        for item in processed_items:
            if item.source not in by_source:
                by_source[item.source] = []
            by_source[item.source].append(item)
        
        # Create digest content
        digest = f"""---
title: "AI News Digest - {date}"
date: {date}
type: daily_digest
item_count: {len(processed_items)}
sources: {len(by_source)}
---

# 🤖 AI News Digest - {date}

**Summary**: {len(processed_items)} articles from {len(by_source)} sources

## 📊 Overview

- **Total Articles**: {len(processed_items)}
- **Unique Sources**: {len(by_source)}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📰 Top Stories

"""
        
        # Add top stories (first 3 items)
        for i, item in enumerate(processed_items[:3]):
            digest += f"""
### {i+1}. {item.title}

**Source**: {item.source} | **Time**: {item.published_date.strftime('%H:%M')}

{item.ai_summary}

[Read Original]({item.url})

---
"""
        
        # Add articles by source
        digest += "\n## 📑 Articles by Source\n\n"
        
        for source, items in by_source.items():
            digest += f"\n### {source} ({len(items)} articles)\n\n"
            
            for item in items:
                digest += f"""
#### [{item.title}]({item.url})
*{item.published_date.strftime('%Y-%m-%d %H:%M')}*

{item.ai_summary}...

---
"""
        
        # Add footer
        digest += f"""
## 🔗 Quick Links

All individual articles have been saved as separate notes in the AI_News/Individual folder.

---
*Digest generated by AI News Aggregator on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        
        return digest

    def extract_tags_from_summary(self, summary: str) -> List[str]:
        """Extract tags from AI summary"""
        default_tags = ['AI', 'news']
        
        # Look for common AI-related keywords
        keywords = {
            'machine learning': 'ML',
            'deep learning': 'DeepLearning', 
            'neural network': 'NeuralNetworks',
            'llm': 'LLM',
            'gpt': 'GPT',
            'chatbot': 'Chatbot',
            'computer vision': 'ComputerVision',
            'nlp': 'NLP',
            'robotics': 'Robotics',
            'autonomous': 'Autonomous',
            'openai': 'OpenAI',
            'google': 'Google',
            'microsoft': 'Microsoft',
            'nvidia': 'NVIDIA',
            'research': 'Research',
            'startup': 'Startup'
        }
        
        found_tags = default_tags.copy()
        summary_lower = summary.lower()
        
        for keyword, tag in keywords.items():
            if keyword in summary_lower:
                found_tags.append(tag)
        
        return list(set(found_tags))  # Remove duplicates

    def save_to_obsidian_comprehensive(self, news_items: List[NewsItem], date: str):
        """Save both individual notes and daily digest"""
        individual_count = self.save_individual_news_to_obsidian(news_items, date)
        
        # Create and save comprehensive digest
        digest_content = self.create_comprehensive_digest(news_items, date)
        digest_saved = self.save_daily_digest_to_obsidian(digest_content, date)
        
        return {
            'individual_notes': individual_count,
            'digest_saved': digest_saved,
            'total_items': len(news_items)
        }