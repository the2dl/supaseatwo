import openai
from rich.console import Console
from rich.panel import Panel
from utils.database import OPENAI_API_KEY

def generate_email_template(topic, recipient_name, url_to_file):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a red team member who works in information security. You are working on a campaign."},
                {"role": "user", "content": f"Write an email to {recipient_name} on the following topic: '{topic}'. In the body, embed the link to the URL: {url_to_file}. Make the email sound professional."}
            ],
        )
        email_template = response.choices[0].message.content.strip()
        return email_template
    except Exception as e:
        print(f"Error generating email template: {e}")
        return None

def display_email_template(template):
    console = Console()
    panel = Panel(template, title="Generated Email Template", border_style="blue")
    console.print(panel)