import openai
from .encryption_utils import encrypt_message
from utils.database import OPENAI_API_KEY

def generate_summary(command, command_output, encryption_key=None):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a red team operator."},
                {"role": "user", "content": f"The following command was executed: '{command}'. Here is the output:\n{command_output}. Summarize this and identify potential next steps for your engagement in 100 words or less."}
            ],
        )
        summary = response.choices[0].message.content.strip()

        if encryption_key:
            encrypted_summary = encrypt_message(summary, encryption_key)
            return encrypted_summary

        return summary
    except Exception as e:
        print(f"Error generating AI summary: {e}")
        return None