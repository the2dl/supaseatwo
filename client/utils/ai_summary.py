import openai

def generate_summary(command_output):
    client = openai.OpenAI(api_key="sk-proj-LQ5dm3iwTPD8Gkg3ys0ET3BlbkFJYrX98APv3iBjcHHRUNEU")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a red team operator."},
                {"role": "user", "content": f"Summarize the following command output:\n{command_output}. Identify potential next steps for your engagement and keep the response brief, 100 words or less."}
            ],
        )
        summary = response.choices[0].message.content.strip()  # Corrected extraction
        return summary
    except Exception as e:
        print(f"Error generating AI summary: {e}")
        return None