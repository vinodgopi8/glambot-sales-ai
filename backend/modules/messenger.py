import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class MessageGenerator:
    def generate(self, lead):
        # Mocking the response to avoid 429 quota errors during UI development
        context = lead.get('description', 'your amazing work')[:100] + "..."
        return f"Hey {lead['name']}, I was just reading about {context}. I think our Glambot 360 booth would be a perfect fit for your upcoming events in {lead.get('location', 'Chennai')}!"
