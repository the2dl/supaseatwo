import openai
from PyQt5.QtCore import QObject, pyqtSignal
from utils.database import OPENAI_API_KEY

class EmailTemplateGenerator(QObject):
    template_generated = pyqtSignal(str)
    generation_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def generate_email_template(self, topic, recipient_name, url_to_file):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional phishing expert."},
                    {"role": "user", "content": f"Write an email to {recipient_name} on the following topic: '{topic}'. In the body, embed the link to the URL: {url_to_file}. Make the email sound professional."}
                ],
            )
            email_template = response.choices[0].message.content.strip()
            self.template_generated.emit(email_template)
            return email_template
        except Exception as e:
            error_message = f"Error generating email template: {e}"
            self.generation_error.emit(error_message)
            return None

email_generator = EmailTemplateGenerator()

def generate_email_template(topic, recipient_name, url_to_file):
    return email_generator.generate_email_template(topic, recipient_name, url_to_file)
