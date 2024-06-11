import openai
from cryptography.fernet import Fernet

def generate_summary(command, command_output, encryption_key=None):
    client = openai.OpenAI(api_key="sk-proj-LQ5dm3iwTPD8Gkg3ys0ET3BlbkFJYrX98APv3iBjcHHRUNEU")

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
            cipher_suite = Fernet(encryption_key)
            encrypted_summary = cipher_suite.encrypt(summary.encode()).decode()
            return encrypted_summary

        return summary
    except Exception as e:
        print(f"Error generating AI summary: {e}")
        return None