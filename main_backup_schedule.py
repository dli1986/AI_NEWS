import schedule
import time
from datetime import datetime
from news_collector import NewsCollector
from llm_processor import LLMProcessor
from output_dispatcher import OutputDispatcher
import sqlite3
from config import NEWS_SOURCES
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AINewsWorkflow:
    def __init__(self):
        self.news_collector = NewsCollector()
        self.llm_processor = LLMProcessor()
        self.output_dispatcher = OutputDispatcher()
    
    def run_daily_workflow(self):
        """执行每日工作流"""
        try:
            print(f"开始执行AI新闻工作流 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. 采集新闻
            print("步骤1: 采集AI新闻...")
            all_sources = []
            for source_list in NEWS_SOURCES.values():
                all_sources.extend(source_list)
            
            news_items = self.news_collector.collect_rss_news(all_sources)
            print(f"采集到 {len(news_items)} 条新闻")
            
            # 2. 处理每条新闻
            print("步骤2: 处理新闻内容...")
            processed_items = []
            for item in news_items:
                # 提取完整内容
                item.content = self.news_collector.extract_full_content(item.url)
                
                # AI总结
                item.ai_summary = self.llm_processor.summarize_news_item(item)
                
                # 保存到数据库
                self.save_news_item(item)
                processed_items.append(item)
                
                print(f"已处理: {item.title[:50]}...")
            
            # 3. 生成日报
            print("步骤3: 生成AI新闻日报...")
            today = datetime.now().strftime('%Y-%m-%d')
            daily_digest = self.llm_processor.generate_daily_digest(processed_items, today)
            
            # 4. 分发输出
            print("步骤4: 分发新闻日报...")
            
            # 发送邮件
            self.output_dispatcher.send_email(
                subject=f"AI新闻日报 - {today}",
                content=daily_digest
            )
            
            # 保存到Obsidian
            self.output_dispatcher.save_to_obsidian(daily_digest, today)
            
            
            print("✅ 工作流执行完成!")
            
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            # 发送错误通知邮件
            self.output_dispatcher.send_email(
                subject="AI新闻工作流执行失败",
                content=f"错误信息: {str(e)}\n时间: {datetime.now()}"
            )
    
    def save_news_item(self, item):
        """保存新闻项到数据库"""
        conn = sqlite3.connect(self.news_collector.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO news_items 
                (title, url, summary, published_date, source, content, ai_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.title,
                item.url,
                item.summary,
                item.published_date.isoformat(),
                item.source,
                item.content,
                item.ai_summary
            ))
            conn.commit()
        except Exception as e:
            print(f"保存新闻失败: {e}")
        finally:
            conn.close()

def main():
    workflow = AINewsWorkflow()
    
    # 设置定时任务 - 每天早上9点执行
    schedule.every().day.at("09:00").do(workflow.run_daily_workflow)
    
    # 也可以立即执行一次测试
    print("执行测试运行...")
    workflow.run_daily_workflow()
    
    # 保持程序运行
    print("定时任务已启动，等待执行...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    main()