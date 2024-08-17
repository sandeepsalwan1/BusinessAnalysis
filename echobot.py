import json
from collections import Counter
from typing import AsyncIterable
import fastapi_poe as fp
from modal import App, Image, asgi_app, exit
from datetime import datetime

# Load the JSON data
with open('cs_chat.json', 'r') as file:
    chat_data = json.load(file)

class AdvancedAnalysisBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        query = request.query[-1].content.lower()
        
        if "analyze" in query:
            analysis = self.analyze_chat_data()
        else:
            analysis = "I can provide in-depth analysis of our customer service chat data with actionable insights. Just ask me to 'analyze the chat data' for a comprehensive report."
        
        yield fp.PartialResponse(text=analysis)

    def analyze_chat_data(self):
        total_conversations = len(chat_data)
        total_messages = sum(len(conv['messages']) for conv in chat_data)
        
        # Analyze messages
        user_messages = Counter()
        assistant_messages = Counter()
        response_times = []
        empathy_scores = []
        sales_technique_scores = []
        games = Counter()
        order_numbers = set()
        
        for conversation in chat_data:
            for event in conversation.get('events', []):
                if event['name'] == 'Empathy and interest assessment':
                    empathy_scores.append(int(event['generated_value']))
                elif event['name'] == 'Sales technique evaluation':
                    sales_technique_scores.append(int(event['generated_value']))
                elif event['name'] == 'Response time':
                    response_times.append(float(event['generated_value']))
                elif event['name'] == 'Game identification':
                    games[event['generated_value']] += 1
                elif event['name'] == 'Order number':
                    order_numbers.add(event['generated_value'])
            
            for message in conversation['messages']:
                if message['role'] == 'user':
                    user_messages[message['content']] += 1
                elif message['role'] == 'assistant':
                    assistant_messages[message['content']] += 1
        
        avg_empathy = sum(empathy_scores) / len(empathy_scores) if empathy_scores else 0
        avg_sales_technique = sum(sales_technique_scores) / len(sales_technique_scores) if sales_technique_scores else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        analysis = "Executive Customer Service Chat Data Analysis:\n\n"
        analysis += f"1. Overview:\n"
        analysis += f"   - Total Conversations: {total_conversations}\n"
        analysis += f"   - Total Messages: {total_messages}\n"
        analysis += f"   - Unique Orders: {len(order_numbers)}\n"
        analysis += f"   - Average Empathy Score: {avg_empathy:.2f}/5\n"
        analysis += f"   - Average Sales Technique Score: {avg_sales_technique:.2f}/5\n"
        analysis += f"   - Average Response Time: {avg_response_time:.2f} seconds\n\n"
        
        analysis += f"2. Top User Queries (Top 5):\n"
        for query, count in user_messages.most_common(5):
            analysis += f"   - {query}: {count} times\n"
        
        analysis += f"\n3. Most Common Bot Responses (Top 5):\n"
        for response, count in assistant_messages.most_common(5):
            analysis += f"   - {response}: {count} times\n"
        
        analysis += f"\n4. Game Distribution (Top 5):\n"
        for game, count in games.most_common(5):
            analysis += f"   - {game}: {count} conversations\n"
        
        analysis += f"\n5. Key Insights:\n"
        if avg_empathy < 3:
            analysis += "   - Empathy scores are below average. Consider additional training for customer service representatives.\n"
        if avg_sales_technique < 3:
            analysis += "   - Sales technique scores need improvement. Review and enhance sales strategies.\n"
        if avg_response_time > 60:
            analysis += "   - Average response time is high. Look into ways to improve response efficiency.\n"
        
        analysis += f"\n6. Recommendations:\n"
        analysis += "   - Focus on improving empathy and sales techniques through targeted training programs.\n"
        analysis += f"   - Optimize response times, especially for the most common user queries.\n"
        analysis += f"   - Consider creating specialized teams for the top games: {', '.join(game for game, _ in games.most_common(3))}.\n"
        
        return analysis

REQUIREMENTS = ["fastapi-poe==0.0.47"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
app = App(name="advanced-analysis-poe", image=image)

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