import sys
import json
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QInputDialog,
)


APP_NAME = "HeartScript Studio"
OLLAMA_URL = "http://127.0.0.1:11434"
PROJECT_DIR = Path.home() / "Documents" / "HeartScript Projects"


# ============================================================
# OLLAMA WORKER
# ============================================================

class OllamaWorker(QObject):
    models_loaded = Signal(list)
    text_received = Signal(str)
    generation_finished = Signal()
    error = Signal(str)

    def load_models(self):
        try:
            with urllib.request.urlopen(
                f"{OLLAMA_URL}/api/tags",
                timeout=5
            ) as response:
                data = json.loads(response.read().decode("utf-8"))

            models = [
                model["name"]
                for model in data.get("models", [])
            ]

            self.models_loaded.emit(models)

        except Exception as exc:
            self.error.emit(
                f"Could not connect to Ollama:\n{exc}"
            )

    def generate(self, model, prompt):
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True
            }

            request = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(
                request,
                timeout=300
            ) as response:

                for line in response:

                    if not line:
                        continue

                    data = json.loads(
                        line.decode("utf-8")
                    )

                    text = data.get("response", "")

                    if text:
                        self.text_received.emit(text)

                    if data.get("done"):
                        break

            self.generation_finished.emit()

        except Exception as exc:
            self.error.emit(
                f"Generation error:\n{exc}"
            )


# ============================================================
# MAIN WINDOW
# ============================================================

class HeartScriptStudio(QMainWindow):

    def __init__(self):

        super().__init__()

        PROJECT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.current_project = None
        self.current_chapter = None
        self.generating = False

        self.worker = OllamaWorker()

        self.worker.models_loaded.connect(
            self.populate_models
        )

        self.worker.text_received.connect(
            self.receive_ai_text
        )

        self.worker.generation_finished.connect(
            self.generation_finished
        )

        self.worker.error.connect(
            self.show_error
        )

        self.setWindowTitle(
            "HeartScript Studio — AI Co-Writing Workbench"
        )

        self.resize(1400, 850)

        self.build_ui()

        self.load_projects()

        self.load_ollama_models()

    # --------------------------------------------------------

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # ====================================================
        # TOP BAR
        # ====================================================

        top_bar = QHBoxLayout()

        title = QLabel(
            "<h2>❤️ HeartScript Studio</h2>"
        )

        subtitle = QLabel(
            "AI Co-Writing Workbench"
        )

        self.model_combo = QComboBox()

        self.model_combo.addItem(
            "Detecting Ollama models..."
        )

        refresh_button = QPushButton(
            "↻ Refresh Models"
        )

        refresh_button.clicked.connect(
            self.load_ollama_models
        )

        new_project_button = QPushButton(
            "＋ New Project"
        )

        new_project_button.clicked.connect(
            self.create_project
        )

        save_button = QPushButton(
            "💾 Save"
        )

        save_button.clicked.connect(
            self.save_current_chapter
        )

        top_bar.addWidget(title)

        top_bar.addWidget(subtitle)

        top_bar.addStretch()

        top_bar.addWidget(
            QLabel("Model:")
        )

        top_bar.addWidget(
            self.model_combo
        )

        top_bar.addWidget(
            refresh_button
        )

        top_bar.addWidget(
            new_project_button
        )

        top_bar.addWidget(
            save_button
        )

        layout.addLayout(top_bar)

        # ====================================================
        # MAIN SPLITTER
        # ====================================================

        splitter = QSplitter(
            Qt.Horizontal
        )

        # ====================================================
        # LEFT PANEL
        # ====================================================

        left_panel = QWidget()

        left_layout = QVBoxLayout(
            left_panel
        )

        left_layout.addWidget(
            QLabel("<h3>📁 Projects</h3>")
        )

        self.project_tree = QTreeWidget()

        self.project_tree.setHeaderLabel(
            "Project Explorer"
        )

        self.project_tree.itemClicked.connect(
            self.tree_item_clicked
        )

        left_layout.addWidget(
            self.project_tree
        )

        new_chapter_button = QPushButton(
            "＋ New Chapter"
        )

        new_chapter_button.clicked.connect(
            self.create_chapter
        )

        left_layout.addWidget(
            new_chapter_button
        )

        splitter.addWidget(
            left_panel
        )

        # ====================================================
        # CENTER PANEL
        # ====================================================

        center_panel = QWidget()

        center_layout = QVBoxLayout(
            center_panel
        )

        self.chapter_title = QLineEdit()

        self.chapter_title.setPlaceholderText(
            "Chapter title..."
        )

        center_layout.addWidget(
            self.chapter_title
        )

        self.editor = QTextEdit()

        self.editor.setPlaceholderText(
            "Start writing your story here..."
        )

        center_layout.addWidget(
            self.editor
        )

        splitter.addWidget(
            center_panel
        )

        # ====================================================
        # RIGHT AI PANEL
        # ====================================================

        right_panel = QWidget()

        right_layout = QVBoxLayout(
            right_panel
        )

        right_layout.addWidget(
            QLabel("<h3>🤖 AI Console</h3>")
        )

        self.prompt_input = QTextEdit()

        self.prompt_input.setPlaceholderText(
            "Describe what you want the AI to write...\n\n"
            "Example:\n"
            "Write a romantic dialogue between Maya and Daniel "
            "after they meet again ten years later."
        )

        self.prompt_input.setMaximumHeight(
            160
        )

        right_layout.addWidget(
            self.prompt_input
        )

        generate_button = QPushButton(
            "✨ Generate"
        )

        generate_button.clicked.connect(
            self.generate
        )

        right_layout.addWidget(
            generate_button
        )

        self.ai_output = QTextEdit()

        self.ai_output.setReadOnly(
            True
        )

        self.ai_output.setPlaceholderText(
            "AI output will appear here token by token..."
        )

        right_layout.addWidget(
            self.ai_output
        )

        insert_button = QPushButton(
            "↓ Insert into Chapter"
        )

        insert_button.clicked.connect(
            self.insert_ai_text
        )

        right_layout.addWidget(
            insert_button
        )

        clear_button = QPushButton(
            "Clear AI Console"
        )

        clear_button.clicked.connect(
            self.ai_output.clear
        )

        right_layout.addWidget(
            clear_button
        )

        splitter.addWidget(
            right_panel
        )

        # Panel proportions

        splitter.setSizes(
            [250, 650, 400]
        )

        layout.addWidget(
            splitter
        )

        # ====================================================
        # STATUS BAR
        # ====================================================

        self.statusBar().showMessage(
            "Ready"
        )

    # ========================================================
    # OLLAMA
    # ========================================================

    def load_ollama_models(self):

        self.statusBar().showMessage(
            "Checking Ollama..."
        )

        thread = threading.Thread(
            target=self.worker.load_models,
            daemon=True
        )

        thread.start()

    def populate_models(self, models):

        self.model_combo.clear()

        if models:

            self.model_combo.addItems(
                models
            )

            self.statusBar().showMessage(
                f"Ollama ready — {len(models)} models found"
            )

        else:

            self.model_combo.addItem(
                "No models installed"
            )

    # ========================================================
    # GENERATION
    # ========================================================

    def generate(self):

        if self.generating:
            return

        model = self.model_combo.currentText()

        prompt = self.prompt_input.toPlainText().strip()

        if not prompt:

            QMessageBox.warning(
                self,
                "No Prompt",
                "Please describe what you want to write."
            )

            return

        if model in [
            "",
            "No models installed"
        ]:
            QMessageBox.warning(
                self,
                "No Model",
                "Please install or select an Ollama model."
            )

            return

        # Add current chapter as context

        chapter_text = self.editor.toPlainText().strip()

        if chapter_text:

            full_prompt = (
                "You are an AI co-writing assistant.\n\n"
                "CURRENT CHAPTER:\n"
                f"{chapter_text[-5000:]}\n\n"
                "WRITING REQUEST:\n"
                f"{prompt}\n\n"
                "Write useful, creative text that fits "
                "the current chapter."
            )

        else:

            full_prompt = prompt

        self.ai_output.clear()

        self.generating = True

        self.statusBar().showMessage(
            f"Generating with {model}..."
        )

        thread = threading.Thread(
            target=self.worker.generate,
            args=(
                model,
                full_prompt
            ),
            daemon=True
        )

        thread.start()

    def receive_ai_text(self, text):

        cursor = self.ai_output.textCursor()

        cursor.movePosition(
            cursor.End
        )

        cursor.insertText(
            text
        )

        self.ai_output.setTextCursor(
            cursor
        )

        self.ai_output.ensureCursorVisible()

    def generation_finished(self):

        self.generating = False

        self.statusBar().showMessage(
            "Generation finished"
        )

    # ========================================================
    # AI OUTPUT
    # ========================================================

    def insert_ai_text(self):

        text = self.ai_output.toPlainText()

        if not text:
            return

        cursor = self.editor.textCursor()

        cursor.insertText(
            text
        )

        self.editor.setTextCursor(
            cursor
        )

        self.statusBar().showMessage(
            "AI text inserted into chapter"
        )

    # ========================================================
    # PROJECT MANAGEMENT
    # ========================================================

    def create_project(self):

        name, ok = QInputDialog.getText(
            self,
            "New Project",
            "Project name:"
        )

        if not ok or not name.strip():
            return

        project_type, ok = QInputDialog.getItem(
            self,
            "Project Type",
            "Choose project type:",
            [
                "Novel",
                "Romance",
                "Dialogue",
                "Courseware"
            ],
            0,
            False
        )

        if not ok:
            return

        safe_name = (
            name.strip()
            .replace("/", "_")
            .replace("\\", "_")
        )

        project_path = PROJECT_DIR / safe_name

        project_path.mkdir(
            exist_ok=True
        )

        project_data = {
            "name": name,
            "type": project_type,
            "created": datetime.now().isoformat(),
            "chapters": []
        }

        with open(
            project_path / "project.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                project_data,
                file,
                indent=2
            )

        self.load_projects()

        self.statusBar().showMessage(
            f"Created project: {name}"
        )

    def load_projects(self):

        self.project_tree.clear()

        for project_path in PROJECT_DIR.iterdir():

            if not project_path.is_dir():
                continue

            project_file = (
                project_path / "project.json"
            )

            if not project_file.exists():
                continue

            try:

                with open(
                    project_file,
                    encoding="utf-8"
                ) as file:

                    data = json.load(file)

                project_item = QTreeWidgetItem(
                    [
                        f"📖 {data['name']} "
                        f"({data.get('type', 'Project')})"
                    ]
                )

                project_item.setData(
                    0,
                    Qt.UserRole,
                    {
                        "type": "project",
                        "path": str(project_path)
                    }
                )

                chapters_dir = (
                    project_path / "chapters"
                )

                if chapters_dir.exists():

                    for chapter_file in sorted(
                        chapters_dir.glob("*.json")
                    ):

                        with open(
                            chapter_file,
                            encoding="utf-8"
                        ) as file:

                            chapter = json.load(file)

                        chapter_item = QTreeWidgetItem(
                            [
                                f"📝 {chapter['title']}"
                            ]
                        )

                        chapter_item.setData(
                            0,
                            Qt.UserRole,
                            {
                                "type": "chapter",
                                "path": str(chapter_file)
                            }
                        )

                        project_item.addChild(
                            chapter_item
                        )

                self.project_tree.addTopLevelItem(
                    project_item
                )

                project_item.setExpanded(
                    True
                )

            except Exception:
                continue

    # ========================================================
    # CHAPTERS
    # ========================================================

    def create_chapter(self):

        project_item = (
            self.project_tree.currentItem()
        )

        if not project_item:

            QMessageBox.warning(
                self,
                "Select Project",
                "Select a project first."
            )

            return

        data = project_item.data(
            0,
            Qt.UserRole
        )

        # If a chapter is selected,
        # use its parent project

        if data and data.get("type") == "chapter":

            project_item = (
                project_item.parent()
            )

            data = project_item.data(
                0,
                Qt.UserRole
            )

        if not data or data.get("type") != "project":

            return

        title, ok = QInputDialog.getText(
            self,
            "New Chapter",
            "Chapter title:"
        )

        if not ok or not title.strip():
            return

        project_path = Path(
            data["path"]
        )

        chapters_dir = (
            project_path / "chapters"
        )

        chapters_dir.mkdir(
            exist_ok=True
        )

        chapter_number = (
            len(
                list(
                    chapters_dir.glob("*.json")
                )
            )
            + 1
        )

        filename = (
            f"{chapter_number:03d}_"
            f"{title.strip().replace(' ', '_')}.json"
        )

        chapter_data = {
            "title": title,
            "content": "",
            "created": datetime.now().isoformat()
        }

        with open(
            chapters_dir / filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                chapter_data,
                file,
                indent=2
            )

        self.load_projects()

    def tree_item_clicked(self, item):

        data = item.data(
            0,
            Qt.UserRole
        )

        if not data:
            return

        if data.get("type") == "chapter":

            path = Path(
                data["path"]
            )

            try:

                with open(
                    path,
                    encoding="utf-8"
                ) as file:

                    chapter = json.load(file)

                self.chapter_title.setText(
                    chapter.get("title", "")
                )

                self.editor.setPlainText(
                    chapter.get("content", "")
                )

                self.current_chapter = path

                self.statusBar().showMessage(
                    f"Loaded: {chapter.get('title')}"
                )

            except Exception as exc:

                self.show_error(
                    str(exc)
                )

    def save_current_chapter(self):

        if not self.current_chapter:

            QMessageBox.warning(
                self,
                "No Chapter",
                "Select or create a chapter first."
            )

            return

        try:

            chapter_data = {
                "title": self.chapter_title.text(),
                "content": self.editor.toPlainText(),
                "updated": datetime.now().isoformat()
            }

            with open(
                self.current_chapter,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    chapter_data,
                    file,
                    indent=2
                )

            self.load_projects()

            self.statusBar().showMessage(
                "Chapter saved"
            )

        except Exception as exc:

            self.show_error(
                str(exc)
            )

    # ========================================================
    # ERRORS
    # ========================================================

    def show_error(self, message):

        self.generating = False

        self.statusBar().showMessage(
            "Error"
        )

        QMessageBox.critical(
            self,
            "HeartScript Studio",
            message
        )


# ============================================================
# APPLICATION
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName(
        APP_NAME
    )

    window = HeartScriptStudio()

    window.show()

    sys.exit(
        app.exec()
    )
