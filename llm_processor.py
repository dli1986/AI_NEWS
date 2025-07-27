import ollama
import json
from typing import List
from news_collector import NewsItem

class LLMProcessor:
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.client = ollama.Client(host=base_url)
    
    def summarize_news_item(self, news_item: NewsItem) -> str:
        """对单条新闻进行AI总结"""
        prompt = f"""
        请对以下AI新闻进行专业总结，要求：
        1. 总结要点不超过200字
        2. 突出技术要点和创新点
        3. 使用Markdown格式
        4. 包含标签分类
        5. 如果原文是英文，请翻译成中文

        标题：{news_item.title}
        来源：{news_item.source}
        原文摘要：{news_item.summary}
        发布时间：{news_item.published_date.strftime('%Y-%m-%d %H:%M')}
        
        请用以下格式回复：
        ## {news_item.title}
        
        **来源**: {news_item.source}  
        **时间**: {news_item.published_date.strftime('%Y-%m-%d')}  
        **标签**: #AI #技术分类
        
        ### 核心要点
        - 要点1
        - 要点2
        - 要点3
        
        ### 技术影响
        简要分析这个新闻对AI领域的影响
        
        ---
        """
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 500
                }
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error summarizing news: {e}")
            return f"总结生成失败: {str(e)}"
    
    def generate_daily_digest(self, news_items: List[NewsItem], date: str) -> str:
        """生成每日AI新闻摘要"""
        summaries = []
        for item in news_items:
            if item.ai_summary:
                summaries.append(item.ai_summary)
        
        digest_prompt = f"""
        基于以下AI新闻总结，生成一份{date}的AI新闻日报，要求：
        1. 开头有日期和新闻条数统计
        2. 按重要性排序
        3. 最后有今日AI行业趋势总结
        4. 使用专业的Markdown格式
        
        新闻总结内容：
        {"".join(summaries)}
        
        请生成完整的日报：
        """
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': digest_prompt
                }],
                options={
                    'temperature': 0.8,
                    'max_tokens': 15000
                }
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error generating daily digest: {e}")
            return f"日报生成失败: {str(e)}"