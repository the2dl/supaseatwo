import openai
from cryptography.fernet import Fernet
from utils.database import OPENAI_API_KEY, get_setting

def generate_summary(command, command_output, encryption_key=None):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Fetch the os value from the settings table
    os_value = get_setting('os')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a red team operator focused on penetration testing and vulnerability assessment. Your goal is to provide concise summaries of command outputs and recommend strategic next steps for further engagement."},
                {"role": "user", "content": f"The following command was executed on {os_value} OS: '{command}'. Here is the output:\n{command_output}. Summarize the results and suggest potential next steps for our red team engagement, keeping your response under 100 words."}
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