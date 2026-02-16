from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QGroupBox,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt
from config.settings import (
    AVAILABLE_OPENAI_MODELS,
    LOCAL_CHAT_MODELS,
    AVAILABLE_BRIEF_MODELS,
    MODEL_PRICING,
    REASONING_EFFORT_OPTIONS,
    get_model_pricing,
    get_display_name,
    get_model_from_display_name,
    supports_reasoning_effort,
    settings,
)


class CostDisplayWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setStyleSheet("""
            CostDisplayWidget {
                background-color: #2D2D2D;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
            }
            QLabel {
                color: #E8E8E8;
            }
            QLabel#costHeader {
                font-weight: bold;
                color: #2196F3;
            }
            QLabel#costValue {
                font-family: monospace;
                color: #4CAF50;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self.header_label = QLabel("API Cost (per million tokens)")
        self.header_label.setObjectName("costHeader")
        layout.addWidget(self.header_label)

        cost_row = QHBoxLayout()
        cost_row.setSpacing(20)

        input_layout = QVBoxLayout()
        input_label = QLabel("Input:")
        input_label.setStyleSheet("font-size: 9pt; color: #B0B0B0;")
        self.input_cost_label = QLabel("$0.00")
        self.input_cost_label.setObjectName("costValue")
        self.input_cost_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_cost_label)

        output_layout = QVBoxLayout()
        output_label = QLabel("Output:")
        output_label.setStyleSheet("font-size: 9pt; color: #B0B0B0;")
        self.output_cost_label = QLabel("$0.00")
        self.output_cost_label.setObjectName("costValue")
        self.output_cost_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_cost_label)

        cost_row.addLayout(input_layout)
        cost_row.addLayout(output_layout)
        cost_row.addStretch()

        layout.addLayout(cost_row)

    def update_costs(self, model_name: str):
        input_cost, output_cost = get_model_pricing(model_name)
        
        if input_cost == 0 and output_cost == 0:
            self.input_cost_label.setText("Free")
            self.output_cost_label.setText("Free")
            self.input_cost_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #4CAF50;")
            self.output_cost_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #4CAF50;")
        else:
            self.input_cost_label.setText(f"${input_cost:.2f}")
            self.output_cost_label.setText(f"${output_cost:.2f}")
            self.input_cost_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #FFA726;")
            self.output_cost_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #FFA726;")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(650, 620)

        vbox = QVBoxLayout(self)

        api_group = QGroupBox("OpenAI API Configuration")
        api_layout = QVBoxLayout()
        
        api_label = QLabel("OpenAI API Key:")
        api_help = QLabel("<small>Required for OpenAI models (gpt-5.2, gpt-5.1, gpt-4o, etc.)</small>")
        api_help.setStyleSheet("color: gray;")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk-proj-...")
        self.api_key_edit.setText(settings.openai_api_key)
        
        self.show_key_btn = QPushButton("Show/Hide")
        self.show_key_btn.setMaximumWidth(100)
        self.show_key_btn.clicked.connect(self._toggle_api_key_visibility)
        
        api_key_row = QHBoxLayout()
        api_key_row.addWidget(self.api_key_edit)
        api_key_row.addWidget(self.show_key_btn)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(api_help)
        api_layout.addLayout(api_key_row)
        api_group.setLayout(api_layout)
        vbox.addWidget(api_group)

        model_group = QGroupBox("Model Settings")
        model_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Brief Model:"))
        self.model_combo = QComboBox()
        for model in AVAILABLE_BRIEF_MODELS:
            self.model_combo.addItem(get_display_name(model), model)
        self._set_combo_by_model(self.model_combo, settings.model)
        row1.addWidget(self.model_combo)
        model_layout.addLayout(row1)

        self.brief_cost_widget = CostDisplayWidget()
        self.brief_cost_widget.update_costs(settings.model)
        model_layout.addWidget(self.brief_cost_widget)

        row_brief_verbosity = QHBoxLayout()
        self.brief_v_label = QLabel("Brief Verbosity:")
        self.brief_v_combo = QComboBox()
        self.brief_v_combo.addItems(["low", "medium", "high"])
        self.brief_v_combo.setCurrentText(settings.brief_verbosity)
        row_brief_verbosity.addWidget(self.brief_v_label)
        row_brief_verbosity.addWidget(self.brief_v_combo)
        model_layout.addLayout(row_brief_verbosity)

        row_brief_reasoning = QHBoxLayout()
        self.brief_r_label = QLabel("Reasoning Effort:")
        self.brief_r_combo = QComboBox()
        self.brief_r_combo.addItems(REASONING_EFFORT_OPTIONS)
        self.brief_r_combo.setCurrentText(settings.brief_reasoning_effort)
        row_brief_reasoning.addWidget(self.brief_r_label)
        row_brief_reasoning.addWidget(self.brief_r_combo)
        model_layout.addLayout(row_brief_reasoning)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet("color: #404040;")
        model_layout.addWidget(separator1)

        row_chat = QHBoxLayout()
        row_chat.addWidget(QLabel("Chat Model:"))
        self.chat_model_combo = QComboBox()
        for model in (LOCAL_CHAT_MODELS + AVAILABLE_OPENAI_MODELS):
            self.chat_model_combo.addItem(get_display_name(model), model)
        self._set_combo_by_model(self.chat_model_combo, settings.chat_model)
        row_chat.addWidget(self.chat_model_combo)
        model_layout.addLayout(row_chat)

        self.chat_cost_widget = CostDisplayWidget()
        self.chat_cost_widget.update_costs(settings.chat_model)
        model_layout.addWidget(self.chat_cost_widget)

        row_chat_verbosity = QHBoxLayout()
        self.chat_v_label = QLabel("Chat Verbosity:")
        self.chat_v_combo = QComboBox()
        self.chat_v_combo.addItems(["low", "medium", "high"])
        self.chat_v_combo.setCurrentText(settings.chat_verbosity)
        row_chat_verbosity.addWidget(self.chat_v_label)
        row_chat_verbosity.addWidget(self.chat_v_combo)
        model_layout.addLayout(row_chat_verbosity)

        row_chat_reasoning = QHBoxLayout()
        self.chat_r_label = QLabel("Reasoning Effort:")
        self.chat_r_combo = QComboBox()
        self.chat_r_combo.addItems(REASONING_EFFORT_OPTIONS)
        self.chat_r_combo.setCurrentText(settings.chat_reasoning_effort)
        row_chat_reasoning.addWidget(self.chat_r_label)
        row_chat_reasoning.addWidget(self.chat_r_combo)
        model_layout.addLayout(row_chat_reasoning)

        model_group.setLayout(model_layout)
        vbox.addWidget(model_group)

        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Default Brief Format:"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["viewer", "prompt_clipboard", "txt", "docx", "pdf"])
        self.fmt_combo.setCurrentText(settings.export_fmt)
        row2.addWidget(self.fmt_combo)
        output_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Briefs Save Directory:"))
        self.dir_edit = QLineEdit()
        self.dir_edit.setReadOnly(True)
        self.dir_edit.setText(settings.briefs_save_dir)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_folder)
        row3.addWidget(self.dir_edit)
        row3.addWidget(browse_btn)
        output_layout.addLayout(row3)

        output_group.setLayout(output_layout)
        vbox.addWidget(output_group)

        vbox.addStretch()

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_row.addStretch(1)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        vbox.addLayout(btn_row)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        self.model_combo.currentIndexChanged.connect(self._on_brief_model_changed)
        self.chat_model_combo.currentIndexChanged.connect(self._on_chat_model_changed)

        self._update_brief_controls_visibility()
        self._update_chat_controls_visibility()

    def _set_combo_by_model(self, combo: QComboBox, model: str) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == model:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)

    def _get_selected_model(self, combo: QComboBox) -> str:
        return combo.currentData() or combo.currentText()

    def _toggle_api_key_visibility(self) -> None:
        if self.api_key_edit.echoMode() == QLineEdit.Password:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)

    def _on_brief_model_changed(self) -> None:
        model = self._get_selected_model(self.model_combo)
        self.brief_cost_widget.update_costs(model)
        self._update_brief_controls_visibility()

    def _on_chat_model_changed(self) -> None:
        model = self._get_selected_model(self.chat_model_combo)
        self.chat_cost_widget.update_costs(model)
        self._update_chat_controls_visibility()

    def _update_brief_controls_visibility(self) -> None:
        model = self._get_selected_model(self.model_combo)
        is_gpt5_family = model.startswith(("gpt-5.1", "gpt-5.2"))
        show_reasoning = supports_reasoning_effort(model)
        self.brief_v_label.setVisible(is_gpt5_family)
        self.brief_v_combo.setVisible(is_gpt5_family)
        self.brief_r_label.setVisible(show_reasoning)
        self.brief_r_combo.setVisible(show_reasoning)

    def _update_chat_controls_visibility(self) -> None:
        model = self._get_selected_model(self.chat_model_combo)
        is_gpt5_family = model.startswith(("gpt-5.1", "gpt-5.2"))
        show_reasoning = supports_reasoning_effort(model)
        self.chat_v_label.setVisible(is_gpt5_family)
        self.chat_v_combo.setVisible(is_gpt5_family)
        self.chat_r_label.setVisible(show_reasoning)
        self.chat_r_combo.setVisible(show_reasoning)

    def _browse_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Case Briefs Folder", self.dir_edit.text())
        if path:
            self.dir_edit.setText(path)

    def accept(self) -> None:
        settings.model = self._get_selected_model(self.model_combo)
        settings.brief_verbosity = self.brief_v_combo.currentText()
        settings.brief_reasoning_effort = self.brief_r_combo.currentText()
        settings.chat_model = self._get_selected_model(self.chat_model_combo)
        settings.chat_verbosity = self.chat_v_combo.currentText()
        settings.chat_reasoning_effort = self.chat_r_combo.currentText()
        settings.export_fmt = self.fmt_combo.currentText()
        settings.briefs_save_dir = self.dir_edit.text()
        settings.openai_api_key = self.api_key_edit.text().strip()
        settings.save_user_prefs()
        super().accept()