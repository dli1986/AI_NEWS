# app.py - Streamlit Web Interface
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from news_collector import NewsCollector
from llm_processor import LLMProcessor
from output_dispatcher import EnhancedOutputDispatcher
from config import NEWS_SOURCES, UI_CONFIG
import asyncio
import threading

# Configure page
st.set_page_config(
    page_title=UI_CONFIG['page_title'],
    page_icon=UI_CONFIG['page_icon'],
    layout=UI_CONFIG['layout']
)

class AINewsApp:
    def __init__(self):
        self.news_collector = NewsCollector()
        self.llm_processor = LLMProcessor()
        self.output_dispatcher = EnhancedOutputDispatcher()
        
        # Initialize session state
        if 'workflow_running' not in st.session_state:
            st.session_state.workflow_running = False
        if 'last_collection' not in st.session_state:
            st.session_state.last_collection = None
        if 'news_data' not in st.session_state:
            st.session_state.news_data = None

    def load_news_from_db(self, days_back=7):
        """Load news from database"""
        conn = sqlite3.connect(self.news_collector.db_path)
        
        query = """
        SELECT * FROM news_items 
        WHERE published_date >= date('now', '-{} days')
        ORDER BY published_date DESC
        """.format(days_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['published_date'] = pd.to_datetime(df['published_date'])
        
        return df

    def run_collection_workflow(self, selected_sources):
        """Run news collection workflow"""
        try:
            with st.spinner("Collecting AI news..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Collect news
                status_text.text("Step 1/3: Collecting news from RSS feeds...")
                progress_bar.progress(33)
                
                all_sources = []
                for category, sources in NEWS_SOURCES.items():
                    if category in selected_sources:
                        all_sources.extend(sources)
                
                news_items = self.news_collector.collect_rss_news(all_sources)
                
                # Step 2: Process content
                status_text.text(f"Step 2/3: Processing {len(news_items)} news items...")
                progress_bar.progress(66)
                
                processed_count = 0
                for item in news_items:
                    # Extract content
                    item.content = self.news_collector.extract_full_content(item.url)
                    
                    # AI summary
                    item.ai_summary = self.llm_processor.summarize_news_item(item)
                    
                    # Save to database
                    self.save_news_item(item)
                    processed_count += 1
                
                """ 
                # Step 3: Generate digest
                status_text.text("Step 3/4: Generating daily digest...")
                progress_bar.progress(75)
                
                today = datetime.now().strftime('%Y-%m-%d')
                daily_digest = self.llm_processor.generate_daily_digest(news_items, today)
                """
              
                # Step 4: Output
                status_text.text("Step 3/3: Saving outputs...")
                progress_bar.progress(90)
                today = datetime.now().strftime('%Y-%m-%d')

                # Save to Obsidian
                self.output_dispatcher.save_to_obsidian_comprehensive(news_items, today)
                
                # Complete
                progress_bar.progress(100)
                status_text.text("✅ Workflow completed successfully!")
                
                st.session_state.last_collection = datetime.now()
                return processed_count
                
        except Exception as e:
            st.error(f"Workflow failed: {str(e)}")
            return 0

    def save_news_item(self, item):
        """Save news item to database"""
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
        finally:
            conn.close()

    def render_dashboard(self):
        """Render main dashboard"""
        st.title("🤖 AI News Aggregator Dashboard")
        
        # Sidebar controls
        st.sidebar.header("Controls")
        
        # Source selection
        st.sidebar.subheader("News Sources")
        selected_sources = []
        for category, sources in NEWS_SOURCES.items():
            if st.sidebar.checkbox(category.replace('_', ' ').title(), value=True):
                selected_sources.append(category)
        
        # Collection controls
        st.sidebar.subheader("Actions")
        if st.sidebar.button("🔄 Collect News", type="primary"):
            count = self.run_collection_workflow(selected_sources)
            if count > 0:
                st.sidebar.success(f"Processed {count} news items!")
                st.rerun()
        
        if st.sidebar.button("📧 Send Email Digest"):
            # Generate and send email digest
            df = self.load_news_from_db(days_back=1)
            if not df.empty:
                today = datetime.now().strftime('%Y-%m-%d')
                news_items = [row for _, row in df.iterrows()]
                digest = self.llm_processor.generate_daily_digest(news_items, today)
                self.output_dispatcher.send_email(
                    subject=f"AI News Digest - {today}",
                    content=digest
                )
                st.sidebar.success("Email sent!")
        
        # Main content
        col1, col2, col3, col4 = st.columns(4)
        
        # Load recent data
        df = self.load_news_from_db(days_back=7)
        
        if df.empty:
            st.warning("No news data found. Click 'Collect News' to get started.")
            return
        
        # Metrics
        with col1:
            st.metric("Total Articles", len(df))
        
        with col2:
            today_count = len(df[df['published_date'].dt.date == datetime.now().date()])
            st.metric("Today's Articles", today_count)
        
        with col3:
            unique_sources = df['source'].nunique()
            st.metric("Unique Sources", unique_sources)
        
        with col4:
            if st.session_state.last_collection:
                last_update = st.session_state.last_collection.strftime("%H:%M")
                st.metric("Last Update", last_update)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Articles by Date")
            daily_counts = df.groupby(df['published_date'].dt.date).size()
            fig = px.line(x=daily_counts.index, y=daily_counts.values,
                         labels={'x': 'Date', 'y': 'Articles'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Sources Distribution")
            source_counts = df['source'].value_counts().head(10)
            fig = px.bar(x=source_counts.values, y=source_counts.index,
                        orientation='h', labels={'x': 'Articles', 'y': 'Source'})
            st.plotly_chart(fig, use_container_width=True)

    def render_news_list(self):
        """Render news list page"""
        st.title("📰 Latest AI News")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        df = self.load_news_from_db(days_back=30)
        
        if df.empty:
            st.warning("No news data available.")
            return
        
        with col1:
            days_filter = st.selectbox("Days Back", [1, 3, 7, 14, 30], index=2)
        
        with col2:
            sources = ['All'] + list(df['source'].unique())
            source_filter = st.selectbox("Source", sources)
        
        with col3:
            search_term = st.text_input("🔍 Search in titles")
        
        # Apply filters
        filtered_df = df[df['published_date'] >= datetime.now() - timedelta(days=days_filter)]
        
        if source_filter != 'All':
            filtered_df = filtered_df[filtered_df['source'] == source_filter]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
        
        # Display news
        st.write(f"Showing {len(filtered_df)} articles")
        
        for _, row in filtered_df.iterrows():
            with st.expander(f"📄 {row['title'][:100]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Source:** {row['source']}")
                    st.write(f"**Published:** {row['published_date']}")
                    st.write(f"**URL:** [{row['url']}]({row['url']})")
                
                with col2:
                    if st.button(f"🤖 Generate Summary", key=f"sum_{row['id']}"):
                        if not row['ai_summary']:
                            # Generate summary if not exists
                            summary = self.llm_processor.summarize_news_item(row)
                            # Update in database
                            conn = sqlite3.connect(self.news_collector.db_path)
                            cursor = conn.cursor()
                            cursor.execute('UPDATE news_items SET ai_summary=? WHERE id=?', 
                                         (summary, row['id']))
                            conn.commit()
                            conn.close()
                            st.rerun()
                
                if row['ai_summary']:
                    st.markdown("**AI Summary:**")
                    st.markdown(row['ai_summary'])
                else:
                    st.write("**Original Summary:**")
                    st.write(row['summary'][:500] + "..." if len(row['summary']) > 500 else row['summary'])

    def render_settings(self):
        """Render settings page"""
        st.title("⚙️ Settings")
        
        tab1, tab2, tab3 = st.tabs(["Sources", "LLM", "Output"])
        
        with tab1:
            st.subheader("News Sources Configuration")
            st.json(NEWS_SOURCES)
            
            st.subheader("Add Custom RSS Feed")
            custom_url = st.text_input("RSS URL")
            if st.button("Add Source"):
                if custom_url:
                    st.success(f"Would add: {custom_url}")
        
        with tab2:
            st.subheader("LLM Configuration")
            model_name = st.text_input("Model Name", value="llama3.1:8b")
            base_url = st.text_input("Ollama URL", value="http://localhost:11434")
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
            
            if st.button("Test LLM Connection"):
                try:
                    # Test connection logic here
                    st.success("LLM connection successful!")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
        
        with tab3:
            st.subheader("Output Configuration")
            st.text_input("Email SMTP Server", placeholder="smtp.gmail.com")
            st.text_input("Obsidian Vault Path", placeholder="C:\ObsidianNote\PKG")

def main():
    app = AINewsApp()
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "News List", "Settings"]
    )
    
    if page == "Dashboard":
        app.render_dashboard()
    elif page == "News List":
        app.render_news_list()
    elif page == "Settings":
        app.render_settings()

if __name__ == "__main__":
    main()