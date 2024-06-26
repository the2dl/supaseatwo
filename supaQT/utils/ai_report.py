import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QTextEdit, QInputDialog
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from utils.database import db_manager
from utils.encryption_utils import decrypt_output, get_encryption_key
import openai
from utils.database import OPENAI_API_KEY

logging.basicConfig(level=logging.ERROR)

class AIReportThread(QThread):
    summary_generated = pyqtSignal(str)
    generation_error = pyqtSignal(str)

    def __init__(self, hostname, custom_prompt):
        super().__init__()
        self.hostname = hostname
        self.custom_prompt = custom_prompt
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def run(self):
        try:
            response = db_manager.get_command_history(self.hostname)
            if response.data:
                commands = response.data
                all_summaries = []
                
                encryption_key = get_encryption_key(self.hostname)
                if not encryption_key:
                    raise ValueError(f"No encryption key found for hostname: {self.hostname}")
                
                for cmd in commands:
                    encrypted_command = cmd['command']
                    encrypted_output = cmd['output']
                    
                    command = decrypt_output(encrypted_command, encryption_key)
                    output = decrypt_output(encrypted_output, encryption_key)
                    
                    if command is None or output is None:
                        continue
                    
                    summary = self.generate_summary(command, output, self.custom_prompt)
                    all_summaries.append(summary)
                
                final_report = self.compile_final_report(self.hostname, all_summaries)
                self.summary_generated.emit(final_report)
            else:
                error_message = f"No command history found for host: {self.hostname}"
                self.generation_error.emit(error_message)
        except Exception as e:
            self.generation_error.emit(str(e))

    def generate_summary(self, command, command_output, custom_prompt):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior red team operator creating an executive-level report."},
                    {"role": "user", "content": f"{custom_prompt}\nCommand: '{command}'\nOutput: {command_output}"}
                ],
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            return f"Error generating summary: {e}"

    def compile_final_report(self, hostname, summaries):
        compiled_summaries = "\n\n".join(summaries)
        final_prompt = f"""
Based on the following summaries of commands executed on the host '{hostname}', create a comprehensive executive-level red team report. When creating this report, please adhere to these guidelines:

1. Start with a brief overall assessment of the security posture (2-3 sentences).
   - Focus on the most significant findings that genuinely impact the organization's security.

2. Highlight the most critical findings across all commands (3-5 bullet points).
   - Only include findings that pose a real and immediate threat to the organization.
   - Prioritize based on potential impact and likelihood of exploitation.
   - Avoid elevating minor issues or standard system behaviors to critical status.

3. Summarize the potential business impacts (1 paragraph).
   - Focus on tangible risks to business operations, data integrity, or reputation.
   - Be realistic about the severity of these impacts.

4. Provide strategic recommendations (3-5 bullet points).
   - Prioritize actions that address the most critical issues first.
   - Suggest practical, high-level solutions rather than technical details.

5. End with a conclusion that includes any positive security aspects and the overall risk level (2-3 sentences).
   - Be balanced in your assessment, acknowledging both strengths and weaknesses.
   - Provide a realistic evaluation of the overall risk level.

Here are the summaries:

{compiled_summaries}

Keep the report concise, avoiding technical jargon, and focus on business risks and strategic implications. The entire report should not exceed 500 words. Remember to maintain a balanced perspective, distinguishing between critical issues and less significant findings.
"""
        return self.generate_executive_report(final_prompt)

    def generate_executive_report(self, executive_prompt):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior red team operator creating an executive-level report."},
                    {"role": "user", "content": executive_prompt}
                ],
            )
            report = response.choices[0].message.content.strip()
            return report
        except Exception as e:
            return f"Error generating executive report: {e}"

class SummaryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        logging.debug("Initializing SummaryTab UI")
        layout = QVBoxLayout()

        self.host_combo = QComboBox()
        self.populate_hosts()
        layout.addWidget(self.host_combo)

        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self.generate_summary)
        layout.addWidget(self.summarize_button)

        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        layout.addWidget(self.summary_display)

        self.setLayout(layout)
        logging.debug("SummaryTab UI initialized")

    def populate_hosts(self):
        logging.debug("Populating hosts")
        response = db_manager.get_hosts()
        if response.data:
            hosts = [host['hostname'] for host in response.data]
            self.host_combo.addItems(hosts)
        logging.debug("Hosts populated")

    def generate_summary(self):
        logging.debug("Generate summary button clicked")
        selected_host = self.host_combo.currentText()
        if selected_host:
            custom_prompt, ok = QInputDialog.getText(self, "Custom Prompt", 
                "Enter your custom prompt for the AI summary (or leave blank for default):")
            
            if ok:
                if not custom_prompt:
                    custom_prompt = """
Generate a concise executive-level summary based on the following command and its output. 
Structure the summary as follows:

1. Brief Description of the Command (1 sentence)
2. Key Findings (1-2 bullet points)
   - Focus only on findings that have significant security implications
   - Avoid elevating minor issues or standard system behaviors
3. Potential Business Impact (1 sentence)
   - Only if the finding poses a real threat to business operations or data
4. Recommended Action (1 sentence, if applicable)
   - Only for issues that require immediate attention

Focus on critical security implications and genuine business risks. Avoid technical jargon and keep the total length to about 75-100 words. If the command or its output doesn't reveal any significant security issues, it's okay to state that no critical findings were identified.
"""
                
                self.summary_display.clear()
                self.summary_display.setPlainText("Generating executive report... Please wait.")
                
                self.report_thread = AIReportThread(selected_host, custom_prompt)
                self.report_thread.summary_generated.connect(self.display_summary)
                self.report_thread.generation_error.connect(self.display_error)
                self.report_thread.start()
                logging.debug("AIReportThread started")

    def display_summary(self, summary):
        logging.debug("Displaying summary")
        self.summary_display.setPlainText(summary)

    def display_error(self, error):
        logging.error(f"Error displayed: {error}")
        self.summary_display.setPlainText(f"Error: {error}")