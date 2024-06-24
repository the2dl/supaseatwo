import openai
from PyQt5.QtCore import QObject, pyqtSignal
from utils.database import OPENAI_API_KEY

class AISummarizer(QObject):
    summary_generated = pyqtSignal(str)
    generation_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def generate_summary(self, command, command_output):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a red team operator."},
                    {"role": "user", "content": f"The following command was executed: '{command}'. Here is the output:\n{command_output}. Summarize this and identify potential next steps for your engagement in 100 words or less."}
                ],
            )
            summary = response.choices[0].message.content.strip()
            self.summary_generated.emit(summary)
            return summary
        except Exception as e:
            error_message = f"Error generating AI summary: {e}"
            self.generation_error.emit(error_message)
            return error_message

ai_summarizer = AISummarizer()

def generate_summary(command, command_output):
    return ai_summarizer.generate_summary(command, command_output)