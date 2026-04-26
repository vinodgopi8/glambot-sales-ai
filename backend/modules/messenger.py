import os
from openai import OpenAI

if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    client = None

class MessageGenerator:
    def generate(self, lead):
        if client:
            # Use OpenAI if key is set
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sales assistant for Glambot 360, a photo booth company. Generate a personalized outreach message for the lead."},
                    {"role": "user", "content": f"Lead: {lead}"}
                ]
            )
            return response.choices[0].message.content
        else:
            # Mocking the response to avoid 429 quota errors during UI development
            context = lead.get('description', 'your amazing work')[:100] + "..."
            return f"Hey {lead['name']}, I was just reading about {context}. I think our Glambot 360 booth would be a perfect fit for your upcoming events in {lead.get('location', 'Chennai')}!"
