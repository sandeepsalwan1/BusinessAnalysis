"""
Advanced chat analysis bot providing insights for company executives.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import AsyncIterable
import fastapi_poe as fp
from modal import App, Image, asgi_app, exit
from collections import Counter
from datetime import datetime

import modal

# Enhanced mock chat data
chat_data = [
    {"user": "Alice", "message": "Hi, I need help with my order #1234. It's been 3 days and hasn't shipped yet.", "timestamp": "2023-08-17 10:00:00"},
    {"user": "Bob", "message": "When will the new Pear Pro model launch? I've been waiting for months!", "timestamp": "2023-08-17 10:15:00"},
    {"user": "Charlie", "message": "The website is extremely slow. I can't complete my purchase.", "timestamp": "2023-08-17 10:30:00"},
    {"user": "David", "message": "Do you offer discounts for bulk orders? I'm looking to purchase 50 units.", "timestamp": "2023-08-17 11:00:00"},
    {"user": "Eve", "message": "I received a damaged product. How can I get a replacement?", "timestamp": "2023-08-17 11:15:00"},
    {"user": "Frank", "message": "Your competitor is offering a 20% discount. Can you match that?", "timestamp": "2023-08-17 11:30:00"},
    {"user": "Grace", "message": "I love the new feature in your app! It's so user-friendly.", "timestamp": "2023-08-17 12:00:00"},
    {"user": "Henry", "message": "Is there a loyalty program for frequent customers?", "timestamp": "2023-08-17 12:15:00"},
    {"user": "Ivy", "message": "The quality of your products has really improved lately. Great job!", "timestamp": "2023-08-17 12:30:00"},
    {"user": "Jack", "message": "I've been on hold for 30 minutes. Your customer service needs improvement.", "timestamp": "2023-08-17 13:00:00"}
]

class AdvancedAnalysisBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        query = request.query[-1].content.lower()
        
        if "analyze" in query:
            analysis = self.analyze_chat_data()
        else:
            analysis = "I can provide in-depth analysis of our chat data with actionable insights. Just ask me to 'analyze the chat data' for a comprehensive report."
        
        yield fp.PartialResponse(text=analysis)

    def analyze_chat_data(self):
        chat_data = json.loads((Path(__file__).parent / FILENAME).read_text())
        total_messages = len(chat_data)
        unique_users = len(set(chat['user'] for chat in chat_data))
        
        # Enhanced topic analysis
        topics = Counter()
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        urgent_issues = []
        
        for chat in chat_data:
            message = chat['message'].lower()
            
            # Topic classification
            if "order" in message or "ship" in message:
                topics['Order Issues'] += 1
            elif "product" in message or "quality" in message:
                topics['Product Feedback'] += 1
            elif "website" in message or "app" in message:
                topics['Technical Issues'] += 1
            elif "discount" in message or "price" in message:
                topics['Pricing Inquiries'] += 1
            elif "customer service" in message:
                topics['Customer Service'] += 1
            
            # Sentiment analysis (simple keyword-based)
            if any(word in message for word in ["love", "great", "improved"]):
                sentiments["positive"] += 1
            elif any(word in message for word in ["slow", "damaged", "problem"]):
                sentiments["negative"] += 1
            else:
                sentiments["neutral"] += 1
            
            # Identify urgent issues
            if "damaged" in message or "waiting for months" in message or "30 minutes" in message:
                urgent_issues.append(chat['message'])
        
        most_common_topic = topics.most_common(1)[0]
        
        analysis = "Executive Chat Data Analysis:\n\n"
        analysis += f"1. Overview:\n"
        analysis += f"   - Total Interactions: {total_messages}\n"
        analysis += f"   - Unique Customers: {unique_users}\n"
        analysis += f"   - Primary Concern: {most_common_topic[0]} ({most_common_topic[1]} mentions)\n\n"
        
        analysis += f"2. Customer Sentiment:\n"
        analysis += f"   - Positive: {sentiments['positive']} ({sentiments['positive']/total_messages*100:.1f}%)\n"
        analysis += f"   - Negative: {sentiments['negative']} ({sentiments['negative']/total_messages*100:.1f}%)\n"
        analysis += f"   - Neutral: {sentiments['neutral']} ({sentiments['neutral']/total_messages*100:.1f}%)\n\n"
        
        analysis += f"3. Key Issues Breakdown:\n"
        for topic, count in topics.most_common():
            analysis += f"   - {topic}: {count} mentions\n"
        
        analysis += f"\n4. Urgent Matters Requiring Immediate Attention:\n"
        for issue in urgent_issues:
            analysis += f"   - {issue}\n"
        
        analysis += f"\n5. Strategic Recommendations:\n"
        if topics['Order Issues'] > 2:
            analysis += "   - Review and optimize the order fulfillment process to reduce delays.\n"
        if topics['Technical Issues'] > 1:
            analysis += "   - Invest in website/app performance improvements to enhance user experience.\n"
        if topics['Pricing Inquiries'] > 1:
            analysis += "   - Consider implementing a competitive pricing strategy or loyalty program.\n"
        if sentiments['negative'] > sentiments['positive']:
            analysis += "   - Conduct a comprehensive customer satisfaction survey to address pain points.\n"
        
        analysis += f"\n6. Positive Highlights:\n"
        analysis += "   - Some customers have noticed product quality improvements.\n"
        analysis += "   - The new app feature has received positive feedback.\n"
        
        analysis += f"\nThis analysis provides a snapshot of current customer sentiments and key areas for improvement. Regular monitoring and action on these insights can significantly enhance customer satisfaction and business performance."
        
        return analysis

# (The rest of the code remains the same as in the previous version)

FILENAME = "cs_chat.json"

REQUIREMENTS = ["fastapi-poe==0.0.47"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
app = App(name="advanced-analysis-poe", image=image, mounts=[modal.Mount.from_local_file(Path(__file__).parent / FILENAME, remote_path=f"/root/{FILENAME}")])

@app.cls(image=image)
class Model:
    access_key: str | None = "NeyayIpnVA3utYFgdRLHloImtmnBEotg"
    bot_name: str | None = "POEHackathon"

    @exit()
    def sync_settings(self):
        if self.bot_name and self.access_key:
            try:
                fp.sync_bot_settings(self.bot_name, self.access_key)
            except Exception:
                print("\nWarning: Bot settings sync failed. See: https://creator.poe.com/docs/server-bots-functional-guides#updating-bot-settings")

    @asgi_app()
    def fastapi_app(self):
        bot = AdvancedAnalysisBot()
        fp.sync_bot_settings(self.bot_name, self.access_key)
        if not self.access_key:
            print("Warning: Running without an access key. Set it before production.")
            app = fp.make_app(bot, allow_without_key=True)
        else:
            app = fp.make_app(bot, access_key=self.access_key)
        return app

@app.local_entrypoint()
def main():
    Model().run.remote()