from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem, QMessageBox, QTextEdit, QGroupBox, QSplitter, QWidget, QInputDialog
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont
from utils.tooltip_utils import apply_tooltips
from core.brief_registry import registry, BriefType, GENERAL_BRIEF_TEMPLATE, TOPIC_BRIEF_TEMPLATE

class BriefTypesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Brief Types")
        self.resize(900, 750)
        self._current_editing_label = None
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        list_label = QLabel("<b>Available Brief Types</b>")
        left_layout.addWidget(list_label)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setToolTip("Select a brief type to view or edit its settings")
        left_layout.addWidget(self.tree)
        list_controls = QVBoxLayout()
        row1 = QHBoxLayout()
        self.new_btn = QPushButton("➕ New Brief Type")
        self.new_btn.setObjectName("new_btn")
        self.new_btn.setToolTip("Create a new brief type")
        self.new_category_btn = QPushButton("📁 New Category")
        self.new_category_btn.setToolTip("Create a new category for organizing brief types")
        row1.addWidget(self.new_btn)
        row1.addWidget(self.new_category_btn)
        row2 = QHBoxLayout()
        self.del_btn = QPushButton("🗑️ Delete Brief Type")
        self.del_btn.setObjectName("del_btn")
        self.del_btn.setToolTip("Delete the selected brief type")
        self.del_category_btn = QPushButton("🗑️ Delete Category")
        self.del_category_btn.setToolTip("Delete an empty category")
        row2.addWidget(self.del_btn)
        row2.addWidget(self.del_category_btn)
        list_controls.addLayout(row1)
        list_controls.addLayout(row2)
        left_layout.addLayout(list_controls)
        self.right_panel_container = QWidget()
        right_container_layout = QVBoxLayout(self.right_panel_container)
        right_container_layout.setContentsMargins(0, 0, 0, 0)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QVBoxLayout()
        name_layout = QVBoxLayout()
        name_label = QLabel("<b>Brief Type Name:</b>")
        name_help = QLabel("<small>This name will appear in the context menu</small>")
        name_help.setStyleSheet("color: gray;")
        self.label_edit = QLineEdit()
        self.label_edit.setObjectName("label_edit")
        self.label_edit.setPlaceholderText("e.g., 'Contract Law Brief' or 'General Case Brief'")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.label_edit)
        name_layout.addWidget(name_help)
        basic_layout.addLayout(name_layout)
        type_category_labels = QHBoxLayout()
        type_label = QLabel("<b>Brief Type:</b>")
        category_label = QLabel("<b>Category:</b>")
        type_category_labels.addWidget(type_label)
        type_category_labels.addWidget(category_label)
        basic_layout.addLayout(type_category_labels)
        type_category_combos = QHBoxLayout()
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["general", "topic"])
        self.kind_combo.setObjectName("kind_combo")
        self.category_combo = QComboBox()
        self.category_combo.setEditable(False)
        type_category_combos.addWidget(self.kind_combo)
        type_category_combos.addWidget(self.category_combo)
        basic_layout.addLayout(type_category_combos)
        type_category_help = QHBoxLayout()
        type_help = QLabel("<small>• <b>General:</b> Analyzes all aspects of the case<br>• <b>Topic:</b> Focuses on a specific legal issue only</small>")
        type_help.setStyleSheet("color: gray;")
        type_help.setWordWrap(True)
        category_help = QLabel("<small>Group related brief types together. Select 'None' for uncategorized briefs.</small>")
        category_help.setStyleSheet("color: gray;")
        category_help.setWordWrap(True)
        type_category_help.addWidget(type_help)
        type_category_help.addWidget(category_help)
        basic_layout.addLayout(type_category_help)
        self.topic_container = QWidget()
        topic_layout = QVBoxLayout(self.topic_container)
        topic_label = QLabel("<b>Legal Topic/Issue:</b>")
        topic_help = QLabel("<small>Specify the legal issue to focus on (e.g., 'standing', 'jurisdiction', 'constitutional violations')</small>")
        topic_help.setStyleSheet("color: gray;")
        topic_help.setWordWrap(True)
        self.topic_edit = QLineEdit()
        self.topic_edit.setObjectName("topic_edit")
        self.topic_edit.setPlaceholderText("e.g., 'qualified immunity' or 'breach of contract'")
        topic_layout.addWidget(topic_label)
        topic_layout.addWidget(self.topic_edit)
        topic_layout.addWidget(topic_help)
        basic_layout.addWidget(self.topic_container)
        self.enabled_chk = QCheckBox("✓ Enable this brief type")
        self.enabled_chk.setChecked(True)
        self.enabled_chk.setObjectName("enabled_chk")
        self.enabled_chk.setToolTip("Unchecked brief types won't appear in the context menu")
        basic_layout.addWidget(self.enabled_chk)
        basic_group.setLayout(basic_layout)
        right_layout.addWidget(basic_group)
        advanced_group = QGroupBox("Advanced Settings (Optional)")
        advanced_layout = QVBoxLayout()
        template_label = QLabel("<b>Custom Template Override:</b>")
        template_help = QLabel("<small>Leave empty to use the default template. Only fill this if you need a completely custom prompt for the AI.</small>")
        template_help.setStyleSheet("color: gray;")
        template_help.setWordWrap(True)
        self.template_edit = QTextEdit()
        self.template_edit.setObjectName("template_edit")
        self.template_edit.setMaximumHeight(100)
        self.template_edit.setPlaceholderText("Optional: Enter a custom prompt template here if you want to override the default...")
        advanced_layout.addWidget(template_label)
        advanced_layout.addWidget(template_help)
        advanced_layout.addWidget(self.template_edit)
        advanced_group.setLayout(advanced_layout)
        right_layout.addWidget(advanced_group)
        preview_group = QGroupBox("Template Preview")
        preview_layout = QVBoxLayout()
        preview_help = QLabel("<small>This is the prompt that will be sent to the AI:</small>")
        preview_help.setStyleSheet("color: gray;")
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(120)
        preview_layout.addWidget(preview_help)
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        right_layout.addStretch()
        self.overlay = QWidget(right_panel)
        self.overlay.setObjectName("overlay")
        self.overlay.setAutoFillBackground(True)
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.addStretch()
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setObjectName("editOverlayBtn")
        self.edit_btn.setProperty("class", "primary")
        self.edit_btn.setMaximumWidth(150)
        overlay_layout.addWidget(self.edit_btn, alignment=Qt.AlignCenter)
        overlay_layout.addStretch()
        right_container_layout.addWidget(right_panel)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel_container)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setToolTip("Save changes to the selected brief type")
        self.save_btn.setProperty("class", "primary")
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setProperty("class", "secondary")
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)
        self._load_tree()
        self._refresh_categories()
        self._set_editing_mode(False)
        self.tree.currentItemChanged.connect(self._on_select)
        self.kind_combo.currentTextChanged.connect(self._toggle_topic_visibility)
        self.kind_combo.currentTextChanged.connect(self._update_preview)
        self.topic_edit.textChanged.connect(self._update_preview)
        self.template_edit.textChanged.connect(self._update_preview)
        self.new_btn.clicked.connect(self._new)
        self.new_category_btn.clicked.connect(self._new_category)
        self.del_category_btn.clicked.connect(self._delete_category)
        self.save_btn.clicked.connect(self._save)
        self.del_btn.clicked.connect(self._delete)
        self.close_btn.clicked.connect(self.accept)
        self.edit_btn.clicked.connect(self._enable_editing)
        self._toggle_topic_visibility()
        apply_tooltips(self, "BriefTypesDialog")
        self.right_panel_container.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.right_panel_container and ev.type() in (QEvent.Resize, QEvent.Show):
            if hasattr(self, 'overlay') and self.overlay.parent():
                p = self.overlay.parent()
                self.overlay.setGeometry(0, 0, p.width(), p.height())
        return super().eventFilter(obj, ev)

    def _set_editing_mode(self, enabled: bool):
        self.label_edit.setEnabled(enabled)
        self.kind_combo.setEnabled(enabled)
        self.category_combo.setEnabled(enabled)
        self.topic_edit.setEnabled(enabled)
        self.template_edit.setEnabled(enabled)
        self.enabled_chk.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        if enabled:
            self.overlay.hide()
        else:
            self.overlay.show()
            self.overlay.raise_()
            right_panel = self.overlay.parent()
            if right_panel:
                self.overlay.setGeometry(0, 0, right_panel.width(), right_panel.height())

    def _enable_editing(self):
        self._set_editing_mode(True)

    def _toggle_topic_visibility(self):
        is_topic = self.kind_combo.currentText() == "topic"
        self.topic_container.setVisible(is_topic)
        self._update_preview()

    def _update_preview(self):
        custom_template = self.template_edit.toPlainText().strip()
        if custom_template:
            self.preview_text.setPlainText(custom_template)
        else:
            kind = self.kind_combo.currentText()
            if kind == "general":
                self.preview_text.setPlainText(GENERAL_BRIEF_TEMPLATE)
            else:
                topic = self.topic_edit.text().strip() or "[TOPIC]"
                template = TOPIC_BRIEF_TEMPLATE.format(topic=topic)
                self.preview_text.setPlainText(template)

    def _refresh_categories(self, selected=None) -> None:
        self.category_combo.clear()
        self.category_combo.addItem("None")
        self.category_combo.addItems(registry.get_categories())
        if selected:
            index = self.category_combo.findText(selected)
            self.category_combo.setCurrentIndex(max(0, index))

    def _new_category(self):
        category_name, ok = QInputDialog.getText(self, "New Category", "Enter a name for the new category:", QLineEdit.Normal, "")
        if ok and category_name.strip():
            category_name = category_name.strip()
            if category_name.lower() == "none":
                QMessageBox.warning(self, "Invalid Name", "'None' is a reserved name and cannot be used as a category.")
                return
            existing_categories = registry.get_categories()
            if category_name in existing_categories:
                QMessageBox.information(self, "Category Exists", f"The category '{category_name}' already exists.")
                return
            self._refresh_categories()
            index = self.category_combo.findText(category_name)
            if index < 0:
                self.category_combo.addItem(category_name)
                index = self.category_combo.findText(category_name)
            self.category_combo.setCurrentIndex(index)
            QMessageBox.information(self, "Category Created", f"Category '{category_name}' has been created.\n\nYou can now assign brief types to this category.")

    def _delete_category(self):
        categories = registry.get_categories()
        if not categories:
            QMessageBox.information(self, "No Categories", "There are no categories to delete.")
            return
        category_name, ok = QInputDialog.getItem(self, "Delete Category", "Select a category to delete:", categories, 0, False)
        if ok and category_name:
            briefs_in_category = registry.get_briefs_by_category(category_name)
            if briefs_in_category:
                reply = QMessageBox.question(self, "Category Not Empty", f"The category '{category_name}' contains {len(briefs_in_category)} brief type(s):\n\n" + "\n".join([f"• {b.label}" for b in briefs_in_category[:5]]) + ("\n..." if len(briefs_in_category) > 5 else "") + "\n\nDo you want to move these brief types to 'None' and delete the category?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    for brief in briefs_in_category:
                        brief.category = None
                        registry.upsert(brief)
                    self._load_tree()
                    self._refresh_categories()
                    QMessageBox.information(self, "Category Deleted", f"Category '{category_name}' has been deleted.\n{len(briefs_in_category)} brief type(s) moved to uncategorized.")
            else:
                reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete the category '{category_name}'?\n\nThis category is empty and can be safely removed.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self._refresh_categories()
                    QMessageBox.information(self, "Category Deleted", f"Category '{category_name}' has been deleted.")

    def _load_tree(self):
        self.tree.clear()
        categorized = {}
        uncategorized = []
        for item in registry.all_items():
            if item.category:
                if item.category not in categorized:
                    categorized[item.category] = []
                categorized[item.category].append(item)
            else:
                uncategorized.append(item)
        for category in sorted(categorized.keys()):
            category_node = QTreeWidgetItem(self.tree)
            category_node.setText(0, f"📁 {category}")
            category_node.setExpanded(False)
            font = category_node.font(0)
            font.setBold(True)
            category_node.setFont(0, font)
            for item in sorted(categorized[category], key=lambda x: x.label.lower()):
                child = QTreeWidgetItem(category_node)
                if item.enabled:
                    if item.kind == "general":
                        child.setText(0, f"   📄 {item.label}")
                    else:
                        child.setText(0, f"   🎯 {item.label}")
                else:
                    child.setText(0, f"   ⚫ {item.label} (disabled)")
                    child.setForeground(0, Qt.gray)
                child.setData(0, Qt.UserRole, item)
        for item in sorted(uncategorized, key=lambda x: x.label.lower()):
            tree_item = QTreeWidgetItem(self.tree)
            if item.enabled:
                if item.kind == "general":
                    tree_item.setText(0, f"📄 {item.label}")
                else:
                    tree_item.setText(0, f"🎯 {item.label}")
            else:
                tree_item.setText(0, f"⚫ {item.label} (disabled)")
                tree_item.setForeground(0, Qt.gray)
            tree_item.setData(0, Qt.UserRole, item)

    def _on_select(self, curr: QTreeWidgetItem, _prev: QTreeWidgetItem):
        if not curr:
            self._clear_form()
            return
        it = curr.data(0, Qt.UserRole)
        if not it:
            self._clear_form()
            return
        self._current_editing_label = it.label
        self.label_edit.setText(it.label)
        self.kind_combo.setCurrentText(it.kind)
        self.topic_edit.setText(it.topic or "")
        self.template_edit.setPlainText(it.template or "")
        self.enabled_chk.setChecked(it.enabled)
        if it.category:
            index = self.category_combo.findText(it.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            else:
                self.category_combo.setCurrentIndex(0)
        else:
            self.category_combo.setCurrentIndex(0)
        self._toggle_topic_visibility()
        self._update_preview()
        self._set_editing_mode(False)

    def _clear_form(self):
        self._current_editing_label = None
        self.label_edit.clear()
        self.kind_combo.setCurrentText("general")
        self.category_combo.setCurrentIndex(0)
        self.topic_edit.clear()
        self.template_edit.clear()
        self.enabled_chk.setChecked(True)
        self._toggle_topic_visibility()
        self._update_preview()

    def _new(self):
        self.tree.clearSelection()
        self._clear_form()
        self._set_editing_mode(True)
        self.label_edit.setFocus()

    def _save(self):
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for this brief type.\n\nThis name will appear in the context menu when you right-click on a case.")
            return
        kind = self.kind_combo.currentText()
        topic = self.topic_edit.text().strip() or None
        template = self.template_edit.toPlainText().strip() or None
        enabled = self.enabled_chk.isChecked()
        category = self.category_combo.currentText().strip()
        if category == "None" or not category:
            category = None
        if kind == "topic" and not (template or topic):
            QMessageBox.warning(self, "Missing Topic", "Topic-focused briefs require either:\n\n1. A legal topic/issue to focus on (recommended), OR\n2. A completely custom template\n\nPlease specify the legal issue this brief should analyze.")
            return
        if self._current_editing_label and self._current_editing_label != label:
            registry.delete(self._current_editing_label)
        registry.upsert(BriefType(label=label, kind=kind, topic=topic, template=template, enabled=enabled, category=category))
        self._current_editing_label = label
        self._load_tree()
        self._refresh_categories()
        self._set_editing_mode(False)
        QMessageBox.information(self, "Saved", f"Brief type '{label}' has been saved successfully!")

    def _delete(self):
        item = self.tree.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Please select a brief type from the list to delete.")
            return
        brief_type = item.data(0, Qt.UserRole)
        if not brief_type:
            QMessageBox.information(self, "Invalid Selection", "Please select a brief type, not a category.")
            return
        lbl = brief_type.label
        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete the brief type:\n\n'{lbl}'?\n\nThis action cannot be undone.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            registry.delete(lbl)
            self._load_tree()
            self._refresh_categories()
            self._clear_form()
            self._set_editing_mode(False)
