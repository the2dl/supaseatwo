import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QListWidget, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QTabWidget, QFileDialog, QInputDialog, QMessageBox, 
                             QListWidgetItem, QTabBar, QStyle, QStyleOptionButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QBrush, QColor, QTextCharFormat, QPainter
from datetime import datetime
from PyQt5.QtWidgets import QTabBar, QStyle
from PyQt5.QtCore import QSize

from utils.host_manager import HostManager
from utils.command_executor import CommandExecutor
from utils.event_viewer import EventViewer
from utils.download import downloader, list_and_download_files, download_selected_file
from utils.upload import uploader
from utils.login import login_manager
from utils.ai_email_template import email_generator
from utils.ai_summary import ai_summarizer, generate_summary
from utils.help import help_manager
from login_window import LoginWindow

class AISummaryThread(QThread):
    summary_ready = pyqtSignal(str)

    def __init__(self, command, output):
        super().__init__()
        self.command = command
        self.output = output

    def run(self):
        summary = ai_summarizer.generate_summary(self.command, self.output)
        self.summary_ready.emit(summary)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Forensics Tool")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize managers and controllers
        self.host_manager = HostManager()
        self.command_executor = CommandExecutor()
        self.event_viewer = EventViewer()
        self.downloader = downloader
        self.uploader = uploader
        self.login_manager = login_manager
        self.email_generator = email_generator
        self.ai_summarizer = ai_summarizer
        self.help_manager = help_manager

        self.current_user = None
        self.command_mappings = {}
        self.open_tabs = {}

        # Create main layout
        main_layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create main tab
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        main_tab.setLayout(main_tab_layout)
        self.tab_widget.addTab(main_tab, "Main")

        # Main splitter
        main_splitter = QSplitter(Qt.Vertical)
        main_tab_layout.addWidget(main_splitter)

        self.full_history = ""

        # Top section
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_widget.setLayout(top_layout)

        # Host selector
        host_selector_widget = self.create_labeled_widget("Host Selection", self.create_host_selector())
        top_layout.addWidget(host_selector_widget, 1)

        # Event viewer and AI Summary
        event_ai_splitter = QSplitter(Qt.Horizontal)
        top_layout.addWidget(event_ai_splitter, 3)

        # Event viewer
        event_viewer_widget = self.create_labeled_widget("History", self.create_event_viewer())
        event_ai_splitter.addWidget(event_viewer_widget)

        # AI Summary
        ai_summary_widget = self.create_labeled_widget("AI Summary", self.create_ai_summary())
        event_ai_splitter.addWidget(ai_summary_widget)

        # Set sizes for event viewer and AI summary
        event_ai_splitter.setSizes([2, 1])  # 2:1 ratio

        main_splitter.addWidget(top_widget)

        # Terminal tabs
        self.terminal_tabs = QTabWidget()
        self.terminal_tabs.setTabBar(ClosableTabBar(self.terminal_tabs))
        self.terminal_tabs.setTabsClosable(True)
        self.terminal_tabs.tabCloseRequested.connect(self.close_terminal_tab)
        main_splitter.addWidget(self.terminal_tabs)

        # Buttons
        button_layout = self.create_buttons()
        main_tab_layout.addLayout(button_layout)

        # Help tab
        help_tab = QWidget()
        help_layout = QVBoxLayout()
        help_tab.setLayout(help_layout)
        self.tab_widget.addTab(help_tab, "Help")

        self.help_display = QTextEdit()
        self.help_display.setReadOnly(True)
        help_layout.addWidget(self.help_display)

        # Set initial sizes
        main_splitter.setSizes([400, 400])

        # Connect signals
        self.connect_signals()

        # Initialize hosts
        self.refresh_hosts()

        # Set the color scheme and styles
        self.set_style()

        # Populate help display
        self.populate_help_display()

    def close_terminal_tab(self, index):
        tab_name = self.terminal_tabs.tabText(index)
        if tab_name in self.open_tabs:
            del self.open_tabs[tab_name]
        self.terminal_tabs.removeTab(index)

    def connect_signals(self):
        self.host_manager.hosts_updated.connect(self.update_host_list)
        self.command_executor.command_output.connect(self.add_terminal_output)
        self.command_executor.command_completed.connect(self.on_command_completed)
        self.event_viewer.new_event.connect(self.update_event_viewer)
        self.downloader.download_progress.connect(self.update_download_progress)
        self.downloader.download_complete.connect(self.on_download_complete)
        self.downloader.download_error.connect(self.on_download_error)
        self.uploader.upload_progress.connect(self.update_upload_progress)
        self.uploader.upload_complete.connect(self.on_upload_complete)
        self.uploader.upload_error.connect(self.on_upload_error)
        self.email_generator.template_generated.connect(self.display_email_template)
        self.email_generator.generation_error.connect(self.display_error)

    def create_labeled_widget(self, label_text, content_widget):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        label = QLabel(label_text)
        layout.addWidget(label)

        layout.addWidget(content_widget)
        return widget

    def create_host_selector(self):
        self.host_selector = QListWidget()
        self.host_selector.itemClicked.connect(self.on_host_selected)
        return self.host_selector

    def create_event_viewer(self):
        history_widget = QWidget()
        layout = QVBoxLayout()
        
        self.event_viewer_widget = QTextEdit()
        self.event_viewer_widget.setReadOnly(True)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_history)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_button)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.event_viewer_widget)
        
        history_widget.setLayout(layout)
        return history_widget

    def search_history(self):
        search_term = self.search_input.text().lower()
        history_text = self.event_viewer_widget.toPlainText()
        
        if search_term:
            records = history_text.split('--------------------------------------------------')
            matching_records = [record for record in records if search_term in record.lower()]
            self.event_viewer_widget.setPlainText('--------------------------------------------------'.join(matching_records))
        else:
            self.event_viewer_widget.setPlainText(self.full_history)

    def clear_search(self):
        self.search_input.clear()
        self.event_viewer_widget.setPlainText(self.full_history)

    def create_ai_summary(self):
        self.ai_summary_display = QTextEdit()
        self.ai_summary_display.setReadOnly(True)
        self.ai_summary_display.setPlaceholderText("No AI summary yet.")
        return self.ai_summary_display

    def create_terminal_widget(self, tab_name, user_host_label_text):
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout()
        terminal_widget.setLayout(terminal_layout)

        terminal = QTextEdit()
        terminal.setReadOnly(True)
        terminal_layout.addWidget(terminal)

        command_input_layout = QHBoxLayout()

        user_host_label = QLabel(user_host_label_text)
        command_input_layout.addWidget(user_host_label)

        command_input = QLineEdit()
        command_input.returnPressed.connect(lambda: self.on_command_enter(tab_name, terminal, command_input))
        command_input_layout.addWidget(command_input)

        terminal_layout.addLayout(command_input_layout)

        return terminal_widget, terminal

    def create_buttons(self):
        button_layout = QHBoxLayout()
        buttons = [
            ("Refresh Hosts", self.refresh_hosts),
            ("Remove Host", self.remove_host),
            ("Upload File", self.upload_file),
            ("Download File", self.download_file),
            ("Help", self.show_help)
        ]
        for text, slot in buttons:
            button = QPushButton(text)
            button.clicked.connect(slot)
            button_layout.addWidget(button)
        return button_layout

    def set_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #282a36;
                color: #f8f8f2;
            }
            QTextEdit, QListWidget, QLineEdit {
                background-color: #21222c;
                color: #f8f8f2;
                border: 1px solid #44475a;
            }
            QPushButton {
                background-color: #44475a;
                color: #f8f8f2;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #6272a4;
            }
            QTabWidget::pane {
                border: 1px solid #44475a;
                background-color: #282a36;
            }
            QTabBar::tab {
                background-color: #44475a;
                color: #f8f8f2;
                padding: 5px;
                border: 1px solid transparent;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #bd93f9;
            }
            QSplitter::handle {
                background-color: #44475a;
                height: 2px;
            }
            QHeaderView::section {
                background-color: #21222c;
                color: #f8f8f2;
                padding: 5px;
                border: none;
            }
            QTableView {
                gridline-color: #191a21;
                background-color: #282a36;
                alternate-background-color: #21222c;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #282a36;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #44475a;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            QLabel {
                background-color: #44475a;
                color: #f8f8f2;
                padding: 5px;
                border: 1px solid #6272a4;
            }
        """)

    def refresh_hosts(self):
        self.host_manager.get_hosts()

    def update_host_list(self, hosts):
        self.host_selector.clear()
        for host in hosts:
            item = QListWidgetItem(f"{host['hostname']} ({host['status']})")
            
            if host['status'] == 'dead':
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor('#FF6347')))
            elif host['status'] == 'likely dead':
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor('orange')))
                
            self.host_selector.addItem(item)

    def on_host_selected(self, item):
        hostname = item.text().split(' (')[0]
        local_user = self.host_manager.get_local_user(hostname)
        agent_id, encryption_key = self.host_manager.get_agent_info(hostname)
        tab_name = f"{hostname}@{agent_id}"
        user_host_label_text = f"{local_user}@{hostname}" if local_user else f"@{hostname}"
        
        if tab_name in self.open_tabs:
            self.terminal_tabs.setCurrentIndex(self.open_tabs[tab_name])
        else:
            terminal_widget, terminal = self.create_terminal_widget(tab_name, user_host_label_text)
            index = self.terminal_tabs.addTab(terminal_widget, tab_name)
            self.open_tabs[tab_name] = index
            self.terminal_tabs.setCurrentIndex(index)

        # Fetch and display events for the selected host
        self.event_viewer.fetch_events(hostname)

        # Clear the AI summary display
        self.ai_summary_display.clear()

    def on_command_enter(self, tab_name, terminal, command_input):
        command = command_input.text()
        command_input.clear()
        hostname = tab_name.split('@')[0]
        self.execute_command(hostname, command, terminal)

    def execute_command(self, hostname, command, terminal):
        if self.current_user is None:
            self.add_terminal_output("Error: No user logged in.", terminal)
            return
        
        agent_id, encryption_key = self.host_manager.get_agent_info(hostname)
        if not agent_id or not encryption_key:
            self.add_terminal_output(f"Error: Unable to fetch agent info for {hostname}", terminal)
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_command = f"{timestamp} [{self.current_user}] ~ {command}\n"
        self.add_terminal_output(formatted_command, terminal, color=QColor('#A0A0A0'))
        
        # Execute the command and get the output and command_id
        output, command_id = self.command_executor.execute_command(hostname, self.current_user, command, encryption_key)
        
        # Generate AI summary
        summary = generate_summary(command, output, command_id, encryption_key)
        
        # Update the terminal with the output and summary
        self.add_terminal_output(f"\n{output}\n", terminal)
        self.add_terminal_output(f"\nAI Summary: {summary}\n", terminal)
        self.add_terminal_output("Command execution finished.\n\n", terminal)
        
        # Update AI summary display
        self.ai_summary_display.setPlainText(summary)

    def on_command_completed(self, command, output, summary):
        current_index = self.terminal_tabs.currentIndex()
        tab_name = self.terminal_tabs.tabText(current_index)

        if tab_name in self.open_tabs:
            tab_index = self.open_tabs[tab_name]
            tab_widget = self.terminal_tabs.widget(tab_index)
            
            if tab_widget:
                terminal = tab_widget.findChild(QTextEdit)
                if terminal:
                    self.add_terminal_output("\n", terminal)
                    self.add_terminal_output(f"\n{output}\n", terminal)
                    self.add_terminal_output("\n", terminal)
                    self.add_terminal_output("Command execution finished.\n", terminal)
                    self.add_terminal_output(f"\nAI Summary: {summary}\n", terminal)

        # Update AI summary display
        self.ai_summary_display.setPlainText(summary)

    def update_history(self, command, output):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_entry = f"{timestamp} - {command}\n{output}\n\n"
        self.event_viewer_widget.append(history_entry)

    def add_terminal_output(self, output, terminal=None, color=None):
        if terminal is None:
            current_index = self.terminal_tabs.currentIndex()
            if current_index != -1:
                current_tab = self.terminal_tabs.widget(current_index)
                terminal = current_tab.findChild(QTextEdit)
        
        if terminal:
            cursor = terminal.textCursor()
            cursor.movePosition(cursor.End)
            if color:
                format = QTextCharFormat()
                format.setForeground(color)
                cursor.setCharFormat(format)
            else:
                format = QTextCharFormat()
                format.setForeground(QColor('white'))  # Set default text color to white
                cursor.setCharFormat(format)
            cursor.insertText(output)
            terminal.setTextCursor(cursor)
            terminal.ensureCursorVisible()
        else:
            print(f"Warning: No terminal available for output: {output}")

    def update_event_viewer(self, event):
        if event == "CLEAR":
            self.event_viewer_widget.clear()
            self.full_history = ""
        else:
            self.full_history = event + "\n--------------------------------------------------\n" + self.full_history
            self.event_viewer_widget.setPlainText(self.full_history)

    def upload_file(self):
        local_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload")
        if local_path:
            remote_path, ok = QInputDialog.getText(self, "Remote Path", "Enter the remote path:")
            if ok:
                hostname = self.get_selected_hostname()
                agent_id = self.host_manager.get_agent_id(hostname)
                self.uploader.upload_file(agent_id, hostname, local_path, remote_path, self.current_user)

    def update_upload_progress(self, progress):
        current_terminal = self.get_current_terminal()
        self.add_terminal_output(progress, current_terminal)

    def on_upload_complete(self, filename, remote_url):
        current_terminal = self.get_current_terminal()
        self.add_terminal_output(f"Upload complete: {filename} is now available at {remote_url}", current_terminal)

    def on_upload_error(self, error):
        current_terminal = self.get_current_terminal()
        self.add_terminal_output(f"Upload error: {error}", current_terminal)

    def download_file(self):
        hostname = self.get_selected_hostname()
        if hostname:
            downloads_list = list_and_download_files(hostname)
            current_terminal = self.get_current_terminal()
            self.add_terminal_output(downloads_list, current_terminal)
            index, ok = QInputDialog.getInt(self, "Select Download", "Enter the number of the file to download:", 1, 1, 100)
            if ok:
                local_path, _ = QFileDialog.getSaveFileName(self, "Save File")
                if local_path:
                    result = download_selected_file(hostname, index, local_path)
                    self.add_terminal_output(result, current_terminal)

    def update_download_progress(self, progress):
        current_terminal = self.get_current_terminal()
        self.add_terminal_output(progress, current_terminal)

    def on_download_complete(self, filename, local_path):
        current_terminal = self.get_current_terminal()
        self.add_terminal_output(f"Download complete: {filename} saved to {local_path}", current_terminal)

    def on_download_error(self, error):
        current_terminal = self.get_current_terminal()
        self.add_terminal_output(f"Download error: {error}", current_terminal)

    def get_selected_hostname(self):
        selected_item = self.host_selector.currentItem()
        if selected_item:
            return selected_item.text().split(' (')[0]
        return None

    def set_current_user(self, username):
        self.current_user = username
        print(f"Logged in as: {username}")

    def generate_email_template(self):
        topic = self.topic_input.text()
        recipient = self.recipient_input.text()
        url = self.url_input.text()
        self.email_generator.generate_email_template(topic, recipient, url)

    def display_email_template(self, template):
        self.email_template_display.setPlainText(template)

    def display_ai_summary(self, summary, terminal):
        self.ai_summary_display.setPlainText(summary)
        self.add_terminal_output("AI Summary generated. Check the AI Summary section.", terminal)

    def show_help(self):
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(self.tab_widget.findChild(QWidget, "Help")))

    def show_detailed_help(self, command):
        help_text = self.help_manager.display_detailed_help(command)
        self.help_display.setPlainText(help_text)
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(self.tab_widget.findChild(QWidget, "Help")))

    def display_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)

    def populate_help_display(self):
        help_text = self.help_manager.display_help(self.command_mappings)
        self.help_display.setPlainText(help_text)

    def get_current_terminal(self):
        current_index = self.terminal_tabs.currentIndex()
        if current_index != -1:
            return self.terminal_tabs.widget(current_index).findChild(QTextEdit)
        return None

    def remove_host(self):
        selected_item = self.host_selector.currentItem()
        if selected_item:
            hostname = selected_item.text().split(' (')[0]
            success = self.host_manager.remove_host(hostname)
            if success:
                self.add_terminal_output(f"Host {hostname} removed successfully.")
                self.refresh_hosts()
            else:
                self.add_terminal_output(f"Failed to remove host: {hostname}")
        else:
            self.add_terminal_output("No host selected for removal.")

class ClosableTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setExpanding(False)

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(size.width() + 30)  # Make tabs slightly wider to accommodate close button
        return size

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        option = QStyleOptionButton()
        option.state = QStyle.State_Enabled | QStyle.State_AutoRaise
        
        for i in range(self.count()):
            option.rect = self.tabRect(i)
            option.rect.adjust(5, 5, -5, -5)
            self.style().drawPrimitive(QStyle.PE_IndicatorTabClose, option, painter, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for i in range(self.count()):
                if self.tabRect(i).contains(event.pos()):
                    close_button_rect = self.tabRect(i)
                    close_button_rect.setLeft(close_button_rect.left() + 5)
                    close_button_rect.setRight(close_button_rect.left() + 20)
                    if close_button_rect.contains(event.pos()):
                        self.tabCloseRequested.emit(i)
                        return
        super().mousePressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    login_window = LoginWindow(login_manager)
    if login_window.exec_() == LoginWindow.Accepted:
        window = MainWindow()
        window.set_current_user(login_window.username_input.text())
        window.show()
        sys.exit(app.exec_())