import os
import logging
from pathlib import Path
import pandas as pd
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTableView,
    QHeaderView,
    QLabel,
    QMessageBox,
    QMenu,
    QApplication,
    QFileDialog,
)
from typing import Optional
from datetime import date
from config.settings import settings, expected_columns
from core.brief_registry import registry
from core.brief_utils import build_prompt, BriefRequest
from core.html_parser import parse_html_content
from data.data_loader import DataLoaderThread
from gui.dialogs.brief_viewer import BriefViewer
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.case_chat_dialog import CaseChatDialog
from gui.models.pandas_model import PandasModel
from gui.widgets.search_bar import SearchBar
from gui.widgets.date_filter_bar import DateFilterBar
from services.case_service import CaseService
from services.search_service import SearchService
from utils.tooltip_utils import apply_tooltips
from utils.helpers import convert_file_url_to_windows_path, is_url, is_local_html_file

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = pd.DataFrame()
        self.search_service = SearchService()
        self.case_service = CaseService()
        self._data_loader_thread = None
        self.status_messages = []
        self._setup_ui()
        self._connect_signals()
        self._load_saved_date_filters()
        self._load_data()

    def _setup_ui(self) -> None:
        self.setWindowTitle(settings.window_title)
        self.setGeometry(*settings.window_geometry)

        file_menu = self.menuBar().addMenu("&File")

        settings_action = QAction("Settings…", self)
        settings_action.setObjectName("action_settings")
        settings_action.triggered.connect(self._show_settings_dialog)

        manage_briefs_action = QAction("Manage Brief Types…", self)
        manage_briefs_action.setObjectName("action_manage_briefs")
        manage_briefs_action.triggered.connect(self._show_manage_briefs_dialog)

        view_chats_action = QAction("View Saved Chats…", self)
        view_chats_action.setObjectName("action_view_chats")
        view_chats_action.triggered.connect(self._show_saved_chats)

        file_menu.addAction(settings_action)
        file_menu.addAction(manage_briefs_action)
        file_menu.addAction(view_chats_action)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)

        self.results_table = QTableView()
        self.results_table.setObjectName("results_table")
        self.results_model = PandasModel()
        self.results_table.setModel(self.results_model)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableView.SelectRows)
        self.results_table.setEditTriggers(QTableView.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layout.addWidget(self.results_table)

        self.search_bar = SearchBar()
        self.search_bar.search_box.setObjectName("search_box")
        self.search_bar.column_selector.setObjectName("column_selector")
        self.search_bar.fuzzy_checkbox.setObjectName("fuzzy_checkbox")
        self.layout.addWidget(self.search_bar)

        self.date_filter_bar = DateFilterBar()
        self.layout.addWidget(self.date_filter_bar)

        self.status_label = QLabel("Loading data…")
        self.status_label.setObjectName("status_label")
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setMinimumHeight(60)
        self.layout.addWidget(self.status_label)

        apply_tooltips(
            root=self,
            section="MainWindow",
            actions={
                "action_settings": settings_action,
                "action_manage_briefs": manage_briefs_action,
            },
        )

    def _show_saved_chats(self) -> None:
        from PySide6.QtWidgets import QListWidget, QListWidgetItem, QDialog, QVBoxLayout, QPushButton, QHBoxLayout
        from services.chat_service import ChatService

        dialog = QDialog(self)
        dialog.setWindowTitle("Saved Conversations")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        chat_service = ChatService()
        conversations = chat_service.list_all_conversations()

        for conv in conversations:
            citation = conv.get('case_citation', '')
            message_count = conv.get('message_count', 0)
            last_updated = conv.get('last_updated') or ""
            date_str = last_updated[:10] if last_updated else "Unknown"
            
            item_text = f"{citation} - {message_count} messages - {date_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, conv['conversation_id'])
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        button_layout = QHBoxLayout()
        open_btn = QPushButton("Open Selected")
        delete_btn = QPushButton("Delete Selected")
        close_btn = QPushButton("Close")

        def open_selected():
            current = list_widget.currentItem()
            if current:
                conv_id = current.data(Qt.UserRole)
                conv = chat_service.load_conversation(conv_id)
                if conv:
                    chat_dialog = CaseChatDialog(self, conv.file_path, conv.case_citation, conv_id)
                    chat_dialog.show()
                    dialog.close()

        def delete_selected():
            current = list_widget.currentItem()
            if current:
                reply = QMessageBox.question(dialog, "Confirm Delete", 
                    "Delete this conversation?", 
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    conv_id = current.data(Qt.UserRole)
                    chat_service.delete_conversation(conv_id)
                    list_widget.takeItem(list_widget.row(current))

        open_btn.clicked.connect(open_selected)
        delete_btn.clicked.connect(delete_selected)
        close_btn.clicked.connect(dialog.close)

        button_layout.addWidget(open_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.exec()

    def _connect_signals(self) -> None:
        self.search_bar.search_requested.connect(self.handle_search_request)
        self.search_service.search_complete.connect(self.handle_search_results)
        self.results_table.doubleClicked.connect(self.handle_double_click)
        self.results_table.clicked.connect(self.handle_single_click)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        self.case_service.brief_chunk.connect(self._on_brief_chunk)
        self.case_service.brief_ready.connect(self._on_brief_done)
        self.case_service.error.connect(lambda m: self.update_status(f"Error: {m}"))
        self.case_service.api_key_missing.connect(self._on_api_key_missing)
        
        self.date_filter_bar.filter_changed.connect(self._on_date_filter_changed)

    def _load_saved_date_filters(self) -> None:
        from_date = None
        if settings.date_filter_from_enabled and settings.date_filter_from_date:
            try:
                from_date = date.fromisoformat(settings.date_filter_from_date)
            except ValueError:
                pass
        
        to_date = None
        if settings.date_filter_to_enabled and settings.date_filter_to_date:
            try:
                to_date = date.fromisoformat(settings.date_filter_to_date)
            except ValueError:
                pass
        
        self.date_filter_bar.set_date_filters(from_date=from_date, to_date=to_date)
        
        if from_date or to_date:
            self.search_service.set_date_filters(from_date=from_date, to_date=to_date)

    def _save_date_filters(self) -> None:
        from_date, to_date = self.date_filter_bar.get_date_filters()
        
        settings.date_filter_from_enabled = from_date is not None
        settings.date_filter_from_date = from_date.isoformat() if from_date else ""
        settings.date_filter_to_enabled = to_date is not None
        settings.date_filter_to_date = to_date.isoformat() if to_date else ""
        
        settings.save_user_prefs()

    def _on_date_filter_changed(self) -> None:
        from_date, to_date = self.date_filter_bar.get_date_filters()
        
        self.search_service.set_date_filters(from_date=from_date, to_date=to_date)
        
        self._save_date_filters()
        
        self._update_date_filter_status(from_date, to_date)

    def _format_date(self, d: date) -> str:
        return d.strftime("%B %d, %Y")

    def _update_date_filter_status(self, from_date, to_date):
        if from_date and to_date:
            msg = f"Date filter: from {self._format_date(from_date)} through {self._format_date(to_date)}"
            self.update_status(msg)
        elif from_date:
            msg = f"Date filter: from {self._format_date(from_date)} onwards"
            self.update_status(msg)
        elif to_date:
            msg = f"Date filter: up through {self._format_date(to_date)}"
            self.update_status(msg)
        else:
            self.update_status("Date filters cleared")

    def _set_widgets_enabled(self, enabled: bool) -> None:
        self.results_table.setEnabled(enabled)
        self.search_bar.setEnabled(enabled)
        self.date_filter_bar.setEnabled(enabled)
        
        for action in self.menuBar().actions():
            action.setEnabled(enabled)

    def _load_data(self) -> None:
        self._set_widgets_enabled(False)
        self.update_status("Loading data, please wait…")
        self._data_loader_thread = DataLoaderThread(settings.database_path)
        self._data_loader_thread.data_loaded.connect(self.handle_data_loaded)
        self._data_loader_thread.error_occurred.connect(self.handle_error)
        self._data_loader_thread.finished.connect(self._data_loader_thread.deleteLater)
        self._data_loader_thread.start()

    def _show_settings_dialog(self) -> None:
        SettingsDialog(self).exec()

    def _set_briefs_folder(self) -> None:
        current = settings.briefs_save_dir
        path = QFileDialog.getExistingDirectory(self, "Select Case Briefs Folder", current)
        if path:
            settings.briefs_save_dir = path
            settings.save_user_prefs()
            self.update_status("Preferences saved")

    def _show_manage_briefs_dialog(self) -> None:
        from gui.dialogs.brief_types_dialog import BriefTypesDialog
        dlg = BriefTypesDialog(self)
        if dlg.exec():
            from core.brief_registry import registry as _reg
            _reg.reload()
            self.update_status("Brief types updated")

    def _show_brief_viewer(self, html_path: str, model_name: str = "") -> None:
        self._viewer = BriefViewer(self, html_path, model_name)
        self._viewer.destroyed.connect(self._on_viewer_destroyed)
        self._viewer.show()

    def _on_viewer_destroyed(self) -> None:
        self._viewer = None

    def handle_search_request(self, column: str, query: str) -> None:
        if column == "file_path" and query.startswith("file:///"):
            converted = convert_file_url_to_windows_path(query)
            self.search_bar.set_search_text(converted)
            self.search_service.schedule_search(column, converted)
            return
        self.search_service.schedule_search(column, query)

    def handle_search_results(self, result) -> None:
        display = result.total_results if self.search_bar.show_fuzzy_results() else result.exact_matches
        self.results_model.update_data(display)
        if result.success:
            fuzz = f"(+ {result.fuzzy_count} fuzzy)" if result.fuzzy_count else ""
            filter_note = ""
            if self.date_filter_bar.has_active_filters():
                from_date, to_date = self.date_filter_bar.get_date_filters()
                
                if from_date and to_date:
                    filter_note = f" [filtered: from {self._format_date(from_date)} through {self._format_date(to_date)}]"
                elif from_date:
                    filter_note = f" [filtered: from {self._format_date(from_date)} onwards]"
                elif to_date:
                    filter_note = f" [filtered: up through {self._format_date(to_date)}]"
            
            self.update_status(f"{result.message} (search {result.duration:.4f}s){filter_note}", fuzz)
        else:
            self.update_status(f"Search failed: {result.message}")

    def handle_data_loaded(self, data: pd.DataFrame) -> None:
        if data.empty:
            QMessageBox.critical(
                self,
                "Data Loading Failed",
                "The Excel file could not be loaded or contains no data.\n\n"
                "Please check:\n"
                "- The file path in settings is correct\n"
                "- The file is not corrupted\n"
                "- The file contains the expected columns\n\n"
                "The application cannot be used without valid data."
            )
            self.update_status("Failed to load data - application disabled")
            return
        
        self.data = data
        self.search_service.set_data(data)
        self.search_bar.set_columns(expected_columns())
        self._set_widgets_enabled(True)
        self.update_status("Data loaded successfully")

    def handle_error(self, msg: str) -> None:
        QMessageBox.critical(
            self,
            "Data Loading Error",
            f"Failed to load the Excel database:\n\n{msg}\n\n"
            "The application cannot be used without valid data.\n"
            "Please check the database file path in Settings."
        )
        self.update_status(f"Error: {msg} - application disabled")

    def handle_double_click(self, index) -> None:
        from utils.helpers import validate_and_resolve_path
        try:
            row = index.row()

            if self.results_model._data.empty or "file_path" not in self.results_model._data.columns:
                QMessageBox.information(self, "Open File", "No 'file_path' column is available for this table.")
                return

            raw_path = str(self.results_model._data.iloc[row]["file_path"]).strip()
            if not raw_path:
                QMessageBox.information(self, "Open File", "This row has an empty file_path.")
                return

            try:
                resolved = validate_and_resolve_path(raw_path, fallback_subdir="Caselaw")
            except FileNotFoundError:
                QMessageBox.information(
                    self,
                    "Open File",
                    f"Could not find the file at:\n\n{raw_path}\n\n"
                    "Also not found in the Caselaw fallback directory."
                )
                return

            QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved)))

        except Exception as e:
            logger.error(f"Double-click open failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def handle_single_click(self, index) -> None:
        if self.results_model._data.empty:
            return
        try:
            col_name = self.results_model._display_columns[index.column()]
            value = str(self.results_model._data.iloc[index.row()][col_name])
            if is_url(value):
                QDesktopServices.openUrl(QUrl(value))
        except (IndexError, KeyError):
            pass

    def show_context_menu(self, position) -> None:
        index = self.results_table.indexAt(position)
        if not index.isValid() or self.results_model._data.empty:
            return
        menu = QMenu(self)

        citation = ""
        file_path = ""
        try:
            if "citation" in self.results_model._data.columns:
                citation = str(self.results_model._data.iloc[index.row()]["citation"])
            if "file_path" in self.results_model._data.columns:
                file_path = str(self.results_model._data.iloc[index.row()]["file_path"])
        except Exception as e:
            logger.error(f"Get citation/file_path error: {e}")

        copy_cell_action = QAction("Copy Cell", self)
        copy_cell_action.triggered.connect(lambda: self.copy_cell_content(index))
        menu.addAction(copy_cell_action)

        if is_local_html_file(file_path):
            copy_text_action = QAction("Copy Case Text", self)
            copy_text_action.triggered.connect(lambda: self.case_service.copy_case_text(file_path))
            menu.addAction(copy_text_action)

            chat_action = QAction("Chat About This Case", self)
            chat_action.triggered.connect(lambda _chk, f=file_path, c=citation: self._open_case_chat(f, c))
            menu.addAction(chat_action)

            general = registry.get_general()
            if general is not None:
                get_case_brief_action = QAction("Get Case Brief", self)
                get_case_brief_action.triggered.connect(
                    lambda _chk, f=file_path, c=citation, t=general.resolved_template(): self._start_streaming_brief(f, c, t)
                )
                menu.addAction(get_case_brief_action)

            menu.addSeparator()

            categorized_briefs = {}
            uncategorized_briefs = []

            for item in registry.list_topics_alpha():
                if item.category:
                    if item.category not in categorized_briefs:
                        categorized_briefs[item.category] = []
                    categorized_briefs[item.category].append(item)
                else:
                    uncategorized_briefs.append(item)

            def _add_brief_action(target_menu, brief_item, f=file_path, c=citation):
                template = brief_item.resolved_template()
                act = QAction(brief_item.label, self)
                act.triggered.connect(lambda _=False, t=template: self._start_streaming_brief(f, c, t))
                target_menu.addAction(act)

            for category in sorted(categorized_briefs.keys()):
                category_menu = QMenu(category, self)
                for item in categorized_briefs[category]:
                    _add_brief_action(category_menu, item)
                menu.addMenu(category_menu)

            for item in uncategorized_briefs:
                _add_brief_action(menu, item)

        menu.exec(self.results_table.viewport().mapToGlobal(position))

    def copy_cell_content(self, index) -> None:
        try:
            col_name = self.results_model._display_columns[index.column()]
            content = str(self.results_model._data.iloc[index.row()][col_name])
            QApplication.clipboard().setText(content)
        except (IndexError, KeyError):
            pass

    def update_status(self, msg: str, extra: str = "") -> None:
        combined = msg + (f" | {extra}" if extra else "")
        self.status_messages.insert(0, combined)
        if len(self.status_messages) > settings.max_status_messages:
            self.status_messages.pop()
        formatted = [
            f"<span style='color: white;'>{m}</span>" if i == 0 else f"<span style='color: #808080;'>{m}</span>"
            for i, m in enumerate(self.status_messages)
        ]
        self.status_label.setText("<br>".join(formatted))

    def _on_api_key_missing(self) -> None:
        reply = QMessageBox.warning(
            self,
            "OpenAI API Key Required",
            "You need to configure your OpenAI API key to use OpenAI models.\n\n"
            "Would you like to open Settings to add your API key?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._show_settings_dialog()

    def _start_streaming_brief(self, file_path: str, citation: str, template: str) -> None:
        request = BriefRequest(
            file_path=file_path,
            citation=citation,
            template=template,
            model=settings.model,
            verbosity=settings.brief_verbosity
        )

        fmt = settings.export_fmt

        if fmt == "viewer":
            self._show_brief_viewer(file_path, request.model)
            self.case_service.generate_case_brief(request)
            return

        if fmt == "prompt_clipboard":
            try:
                from core.html_parser import parse_html_content
                case_text = parse_html_content(file_path)
                from core.brief_utils import build_prompt
                prompt = build_prompt(request, case_text)
                QApplication.clipboard().setText(prompt)
                self.update_status("Prompt copied to clipboard")
            except Exception as e:
                logger.error(f"Failed to copy prompt: {e}", exc_info=True)
                self.update_status(f"Failed to copy prompt: {e}")
            return

        save_dir = Path(settings.briefs_save_dir)

        if not self._validate_save_directory(save_dir):
            reply = QMessageBox.warning(
                self,
                "Invalid Save Location",
                f"The configured save location does not exist or is not accessible:\n\n"
                f"{save_dir}\n\n"
                f"This may be a disconnected network drive or invalid path.\n\n"
                f"What would you like to do?",
                QMessageBox.Open | QMessageBox.Ignore | QMessageBox.Cancel,
                QMessageBox.Open
            )

            if reply == QMessageBox.Open:
                self._show_settings_dialog()
                return
            elif reply == QMessageBox.Ignore:
                self._show_brief_viewer(file_path)
                self.case_service.generate_case_brief(request)
                return
            else:
                return

        from core.brief_utils import build_brief_path
        from utils.helpers import save_brief
        save_path = build_brief_path(file_path, fmt)

        def _save_and_notify(text):
            try:
                save_brief(text, save_path, fmt)
                self.update_status(f"Brief saved to {save_path}")
            except Exception as e:
                logger.error(f"Save failed: {e}", exc_info=True)
                self.update_status(f"Save failed: {e}")
            finally:
                self.case_service.brief_ready.disconnect(_save_and_notify)

        self.case_service.brief_ready.connect(_save_and_notify)
        self.case_service.generate_case_brief(request)

    def _validate_save_directory(self, dir_path: Path) -> bool:
        try:
            if dir_path.exists():
                return dir_path.is_dir()

            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except (FileNotFoundError, OSError, PermissionError):
            return False

    def _on_brief_chunk(self, text: str) -> None:
        if getattr(self, "_viewer", None) is not None:
            self._viewer.append_chunk(text)

    def _on_brief_done(self, _full: str) -> None:
        if getattr(self, "_viewer", None) is not None:
            self._viewer.finish()

    def _open_case_chat(self, file_path: str, citation: str) -> None:
        try:
            chat_dialog = CaseChatDialog(self, file_path, citation)
            chat_dialog.show()
        except Exception as e:
            logger.error(f"Failed to open chat: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open chat: {e}")