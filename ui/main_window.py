"""
ui/main_window.py
-----------------
Main PySide2 window for Maya Tech System.
Three tabs: Cleaner · Validator · Exporter
"""

import os
import maya.cmds as cmds
import maya.OpenMayaUI as omui

from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance

from maya_tech_system_v2.cleaner.cleaner       import SceneCleaner
from maya_tech_system_v2.validator.validator   import AssetValidator, ValidationItem
from maya_tech_system_v2.exporter.exporter     import FBXExporter
from maya_tech_system_v2.exporter.config       import FBX_PRESETS
from maya_tech_system_v2.core                  import utils


# Maya parent window helper 

def get_maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


# Stylesheet

STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
}

QTabBar::tab {
    background: #333333;
    color: #aaaaaa;
    padding: 8px 20px;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    background: #2b2b2b;
    color: #f0a500;
    border-bottom: 2px solid #f0a500;
}

QPushButton {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 26px;
}

QPushButton:hover {
    background-color: #484848;
    border-color: #f0a500;
}

QPushButton:pressed {
    background-color: #f0a500;
    color: #1a1a1a;
}

QPushButton#btn_primary {
    background-color: #f0a500;
    color: #1a1a1a;
    font-weight: bold;
    border: none;
}

QPushButton#btn_primary:hover {
    background-color: #ffbb33;
}

QPushButton#btn_danger {
    background-color: #6b2020;
    border-color: #aa3333;
}

QPushButton#btn_danger:hover {
    background-color: #883333;
}

QLineEdit, QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 3px;
    padding: 4px 8px;
    color: #e0e0e0;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #f0a500;
}

QCheckBox {
    spacing: 8px;
    color: #cccccc;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #555555;
    background: #1e1e1e;
}

QCheckBox::indicator:checked {
    background: #f0a500;
    border-color: #f0a500;
}

QTreeWidget {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    alternate-background-color: #222222;
}

QTreeWidget::item {
    padding: 4px 2px;
}

QTreeWidget::item:selected {
    background-color: #3a3a1a;
    color: #f0a500;
}

QHeaderView::section {
    background-color: #333333;
    color: #aaaaaa;
    padding: 4px;
    border: none;
    border-right: 1px solid #444444;
}

QLabel#label_section {
    color: #f0a500;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

QLabel#label_status {
    color: #888888;
    font-size: 11px;
    padding: 4px;
}

QFrame#separator {
    border: none;
    border-top: 1px solid #3a3a3a;
    max-height: 1px;
}

QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    color: #888888;
    font-size: 11px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    color: #888888;
}
"""


# Result Tree Item 

def make_tree_item(parent, col0, col1="", level="info"):
    item = QtWidgets.QTreeWidgetItem(parent)
    item.setText(0, col0)
    item.setText(1, col1)

    colors = {
        "error":   "#ff6b6b",
        "warning": "#f0a500",
        "ok":      "#6bcb77",
        "info":    "#aaaaaa",
    }
    color = QtGui.QColor(colors.get(level, "#aaaaaa"))
    for col in range(2):
        item.setForeground(col, color)

    return item


# Main Window 

class MayaTechWindow(QtWidgets.QDialog):

    WINDOW_TITLE = "Maya Tech System  ·  v2.0"

    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(480)
        self.setMinimumHeight(600)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)

        # Module instances (created fresh each run)
        self._cleaner   = None
        self._validator = None
        self._exporter  = FBXExporter()

        self._build_ui()

    # Build UI

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Header
        header = QtWidgets.QLabel("MAYA TECH SYSTEM")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size:16px; font-weight:bold; color:#f0a500; "
                             "letter-spacing:4px; padding:8px 0;")
        root.addWidget(header)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._build_cleaner_tab(),  "⚙  Cleaner")
        self.tabs.addTab(self._build_validator_tab(), "✔  Validator")
        self.tabs.addTab(self._build_exporter_tab(),  "↗  Exporter")
        root.addWidget(self.tabs)

        # Status bar
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setObjectName("label_status")
        self.status_label.setAlignment(QtCore.Qt.AlignRight)
        root.addWidget(self.status_label)

    # Cleaner Tab

    def _build_cleaner_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Operations group
        ops_group = QtWidgets.QGroupBox("Operations")
        ops_layout = QtWidgets.QVBoxLayout(ops_group)

        self.cb_history  = QtWidgets.QCheckBox("Delete Construction History")
        self.cb_freeze   = QtWidgets.QCheckBox("Freeze Transforms")
        self.cb_unused   = QtWidgets.QCheckBox("Delete Unused Nodes")
        self.cb_empty    = QtWidgets.QCheckBox("Delete Empty Groups")
        self.cb_ngons    = QtWidgets.QCheckBox("Fix N-gons  (quadrangulate → triangulate)")
        self.cb_pivots   = QtWidgets.QCheckBox("Fix Pivots to World Origin")
        self.cb_naming   = QtWidgets.QCheckBox("Fix Naming  (apply prefix/suffix to existing names)")

        for cb in (self.cb_history, self.cb_freeze, self.cb_unused, self.cb_empty):
            cb.setChecked(True)
            ops_layout.addWidget(cb)

        # Separator line inside group
        sep_ops = QtWidgets.QFrame()
        sep_ops.setFrameShape(QtWidgets.QFrame.HLine)
        sep_ops.setStyleSheet("border-top: 1px solid #3a3a3a; margin: 4px 0;")
        ops_layout.addWidget(sep_ops)

        for cb in (self.cb_ngons, self.cb_pivots, self.cb_naming):
            cb.setChecked(False)
            ops_layout.addWidget(cb)

        layout.addWidget(ops_group)

        # Rename group
        rename_group = QtWidgets.QGroupBox("Rename Meshes  (optional)")
        rename_layout = QtWidgets.QFormLayout(rename_group)
        rename_layout.setSpacing(8)

        self.field_prefix    = QtWidgets.QLineEdit()
        self.field_suffix    = QtWidgets.QLineEdit()
        self.field_base_name = QtWidgets.QLineEdit()

        self.field_prefix.setPlaceholderText("e.g.  SM")
        self.field_suffix.setPlaceholderText("e.g.  LOD0")
        self.field_base_name.setPlaceholderText("e.g.  Rock  (overrides original name)")

        rename_layout.addRow("Prefix", self.field_prefix)
        rename_layout.addRow("Suffix", self.field_suffix)
        rename_layout.addRow("Base Name", self.field_base_name)
        layout.addWidget(rename_group)

        # Actions
        btn_run = QtWidgets.QPushButton("Run Cleaner")
        btn_run.setObjectName("btn_primary")
        btn_run.clicked.connect(self._run_cleaner)
        layout.addWidget(btn_run)

        sep = QtWidgets.QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        layout.addWidget(sep)

        lbl = QtWidgets.QLabel("N-GON TOOLS")
        lbl.setObjectName("label_section")
        layout.addWidget(lbl)

        row = QtWidgets.QHBoxLayout()
        btn_sel_mesh  = QtWidgets.QPushButton("Select Problem Meshes")
        btn_sel_faces = QtWidgets.QPushButton("Select N-gon Faces")
        btn_fix_ngons = QtWidgets.QPushButton("Fix N-gons")
        btn_fix_ngons.setObjectName("btn_danger")

        btn_sel_mesh.clicked.connect(self._select_problem_meshes)
        btn_sel_faces.clicked.connect(self._select_ngon_faces)
        btn_fix_ngons.clicked.connect(self._fix_ngons)

        row.addWidget(btn_sel_mesh)
        row.addWidget(btn_sel_faces)
        row.addWidget(btn_fix_ngons)
        layout.addLayout(row)

        layout.addStretch()
        return widget

    # Validator Tab 

    def _build_validator_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Result tree
        self.result_tree = QtWidgets.QTreeWidget()
        self.result_tree.setColumnCount(2)
        self.result_tree.setHeaderLabels(["Object", "Issue"])
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setRootIsDecorated(True)
        self.result_tree.header().setStretchLastSection(True)
        self.result_tree.setColumnWidth(0, 180)
        layout.addWidget(self.result_tree)

        # Buttons
        row = QtWidgets.QHBoxLayout()
        btn_validate = QtWidgets.QPushButton("Run Validator")
        btn_validate.setObjectName("btn_primary")
        btn_fix_all  = QtWidgets.QPushButton("Fix All (Auto)")

        btn_validate.clicked.connect(self._run_validator)
        btn_fix_all.clicked.connect(self._fix_all)

        row.addWidget(btn_validate)
        row.addWidget(btn_fix_all)
        layout.addLayout(row)

        return widget

    # Exporter Tab 

    def _build_exporter_tab(self):
        widget = QtWidgets.QWidget()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        scroll.setWidget(inner)
        outer = QtWidgets.QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Export Path 
        lbl_path = QtWidgets.QLabel("EXPORT PATH")
        lbl_path.setObjectName("label_section")
        layout.addWidget(lbl_path)

        path_row = QtWidgets.QHBoxLayout()
        self.field_export_path = QtWidgets.QLineEdit()
        self.field_export_path.setPlaceholderText("Select Unreal Content folder…")
        self.field_export_path.textChanged.connect(self._update_preview)
        btn_browse = QtWidgets.QPushButton("Browse")
        btn_browse.clicked.connect(self._browse_export_path)
        path_row.addWidget(self.field_export_path)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        # ── Preset  
        self._add_sep(layout)
        lbl_preset = QtWidgets.QLabel("FBX PRESET")
        lbl_preset.setObjectName("label_section")
        layout.addWidget(lbl_preset)

        self.combo_preset = QtWidgets.QComboBox()
        for key, val in FBX_PRESETS.items():
            self.combo_preset.addItem(f"{key}  —  {val['description']}", key)
        self.combo_preset.currentIndexChanged.connect(self._update_preview)
        layout.addWidget(self.combo_preset)

        # ── Scale  ─
        self._add_sep(layout)
        lbl_scale = QtWidgets.QLabel("EXPORT SCALE")
        lbl_scale.setObjectName("label_section")
        layout.addWidget(lbl_scale)

        scale_group = QtWidgets.QGroupBox()
        scale_layout = QtWidgets.QHBoxLayout(scale_group)
        scale_layout.setSpacing(8)

        lbl_scale_val = QtWidgets.QLabel("Scale factor:")
        lbl_scale_val.setStyleSheet("color:#aaa; font-size:11px;")
        self.spin_scale = QtWidgets.QDoubleSpinBox()
        self.spin_scale.setRange(0.001, 1000.0)
        self.spin_scale.setValue(1.0)
        self.spin_scale.setDecimals(3)
        self.spin_scale.setFixedWidth(90)
        self.spin_scale.setStyleSheet("background:#1a1a1a; color:#e0e0e0; border:1px solid #444; border-radius:3px; padding:3px;")

        btn_scale_1   = QtWidgets.QPushButton("1.0")
        btn_scale_100 = QtWidgets.QPushButton("100.0  (cm→m)")
        for b in (btn_scale_1, btn_scale_100):
            b.setFixedHeight(24)
            b.setStyleSheet("font-size:11px; padding: 0 8px;")
        btn_scale_1.clicked.connect(lambda: self.spin_scale.setValue(1.0))
        btn_scale_100.clicked.connect(lambda: self.spin_scale.setValue(100.0))

        scale_layout.addWidget(lbl_scale_val)
        scale_layout.addWidget(self.spin_scale)
        scale_layout.addWidget(btn_scale_1)
        scale_layout.addWidget(btn_scale_100)
        scale_layout.addStretch()
        layout.addWidget(scale_group)

        # Options
        self._add_sep(layout)
        lbl_opts = QtWidgets.QLabel("OPTIONS")
        lbl_opts.setObjectName("label_section")
        layout.addWidget(lbl_opts)

        self.cb_one_file_each    = QtWidgets.QCheckBox("One FBX per object  (uncheck for batch into one file)")
        self.cb_export_scene     = QtWidgets.QCheckBox("Export entire scene  (ignores selection)")
        self.cb_use_subfolder    = QtWidgets.QCheckBox("Create subfolder per preset  (e.g. …/StaticMesh/)")
        self.cb_overwrite_protect = QtWidgets.QCheckBox("Overwrite protection  (warn before replacing existing files)")
        self.cb_validate_first   = QtWidgets.QCheckBox("Validate before export  (block on errors)")

        self.cb_one_file_each.setChecked(True)
        self.cb_export_scene.setChecked(False)
        self.cb_use_subfolder.setChecked(False)
        self.cb_overwrite_protect.setChecked(True)
        self.cb_validate_first.setChecked(True)

        for cb in (self.cb_one_file_each, self.cb_export_scene,
                   self.cb_use_subfolder, self.cb_overwrite_protect,
                   self.cb_validate_first):
            cb.stateChanged.connect(self._update_preview)
            layout.addWidget(cb)

        # Export scene disables one-file-each (mutually exclusive)
        self.cb_export_scene.stateChanged.connect(
            lambda state: self.cb_one_file_each.setEnabled(not bool(state))
        )

        # Path Preview
        self._add_sep(layout)
        lbl_prev = QtWidgets.QLabel("PATH PREVIEW")
        lbl_prev.setObjectName("label_section")
        layout.addWidget(lbl_prev)

        self.preview_tree = QtWidgets.QTreeWidget()
        self.preview_tree.setColumnCount(2)
        self.preview_tree.setHeaderLabels(["Object", "Output Path"])
        self.preview_tree.setAlternatingRowColors(True)
        self.preview_tree.header().setStretchLastSection(True)
        self.preview_tree.setColumnWidth(0, 160)
        self.preview_tree.setMaximumHeight(110)
        layout.addWidget(self.preview_tree)

        btn_refresh_prev = QtWidgets.QPushButton("Refresh Preview")
        btn_refresh_prev.clicked.connect(self._update_preview)
        layout.addWidget(btn_refresh_prev)

        # Export Button
        self._add_sep(layout)
        btn_export = QtWidgets.QPushButton("Export")
        btn_export.setObjectName("btn_primary")
        btn_export.setMinimumHeight(36)
        btn_export.clicked.connect(self._run_export)
        layout.addWidget(btn_export)

        # Export Log
        lbl_log = QtWidgets.QLabel("EXPORT LOG")
        lbl_log.setObjectName("label_section")
        layout.addWidget(lbl_log)

        self.export_tree = QtWidgets.QTreeWidget()
        self.export_tree.setColumnCount(3)
        self.export_tree.setHeaderLabels(["Object", "Status", "Time"])
        self.export_tree.setAlternatingRowColors(True)
        self.export_tree.header().setStretchLastSection(False)
        self.export_tree.setColumnWidth(0, 150)
        self.export_tree.setColumnWidth(1, 200)
        self.export_tree.setColumnWidth(2, 80)
        layout.addWidget(self.export_tree)

        # History + Report row
        hist_row = QtWidgets.QHBoxLayout()
        btn_history = QtWidgets.QPushButton("Show Session History")
        btn_report  = QtWidgets.QPushButton("Export Report (.txt)")
        btn_clear   = QtWidgets.QPushButton("Clear Log")
        btn_history.clicked.connect(self._show_history)
        btn_report.clicked.connect(self._export_report)
        btn_clear.clicked.connect(self._clear_export_log)
        hist_row.addWidget(btn_history)
        hist_row.addWidget(btn_report)
        hist_row.addWidget(btn_clear)
        layout.addLayout(hist_row)

        return widget

    # Actions — Cleaner

    def _run_cleaner(self):
        self._cleaner = SceneCleaner()
        data = self._cleaner.run(
            prefix              = self.field_prefix.text().strip(),
            suffix              = self.field_suffix.text().strip(),
            base_name           = self.field_base_name.text().strip(),
            delete_history      = self.cb_history.isChecked(),
            freeze_transforms   = self.cb_freeze.isChecked(),
            delete_unused       = self.cb_unused.isChecked(),
            delete_empty_groups = self.cb_empty.isChecked(),
            fix_ngons           = self.cb_ngons.isChecked(),
            fix_pivots          = self.cb_pivots.isChecked(),
            fix_naming          = self.cb_naming.isChecked(),
        )
        stats = data["stats"]
        ngons = len(data["ngon_faces"])
        msg   = (f"Cleaner done — history:{stats['history']}  "
                 f"frozen:{stats['frozen']}  "
                 f"groups:{stats['empty_groups']}  "
                 f"renamed:{stats['renamed']}  "
                 f"ngons:{ngons}")
        self._set_status(msg)
        utils.show_message("Cleaner Done")

    def _select_problem_meshes(self):
        if self._cleaner and self._cleaner.problematic_meshes:
            cmds.select(self._cleaner.problematic_meshes)
            self._set_status(f"Selected {len(self._cleaner.problematic_meshes)} problem meshes")
        else:
            self._set_status("Run Cleaner first")

    def _select_ngon_faces(self):
        if self._cleaner and self._cleaner.problematic_faces:
            cmds.select(self._cleaner.problematic_faces)
            self._set_status(f"Selected {len(self._cleaner.problematic_faces)} n-gon faces")
        else:
            self._set_status("Run Cleaner first (or no n-gons found)")

    def _fix_ngons(self):
        if not self._cleaner:
            self._cleaner = SceneCleaner()
            self._cleaner.detect_ngons()
        count = self._cleaner.fix_ngons()
        self._set_status(f"Fixed {count} n-gon faces")

    # Actions — Validator

    def _run_validator(self):
        self._validator = AssetValidator()
        data = self._validator.run()
        self._populate_result_tree(data["items"])
        self._set_status(
            f"Validation — {len(data['errors'])} error(s)  {len(data['warnings'])} warning(s)"
        )

    def _fix_all(self):
        if not self._cleaner:
            self._cleaner = SceneCleaner()
        if not self._validator:
            self._validator = AssetValidator()
        self._validator.fix_all(self._cleaner)
        self._run_validator()
        self._set_status("Fix All completed — re-validated")

    def _populate_result_tree(self, items):
        self.result_tree.clear()

        errors_root   = QtWidgets.QTreeWidgetItem(self.result_tree, ["❌  Errors"])
        warnings_root = QtWidgets.QTreeWidgetItem(self.result_tree, ["⚠   Warnings"])

        errors_root.setForeground(0, QtGui.QColor("#ff6b6b"))
        warnings_root.setForeground(0, QtGui.QColor("#f0a500"))

        for item in items:
            level = "error" if item.level == ValidationItem.ERROR else "warning"
            parent = errors_root if level == "error" else warnings_root
            make_tree_item(parent, item.obj, f"{item.check}: {item.message}", level)

        self.result_tree.expandAll()

    # Actions — Exporter

    def _add_sep(self, layout):
        sep = QtWidgets.QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        layout.addWidget(sep)

    def _browse_export_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Unreal Content Folder", ""
        )
        if path:
            self.field_export_path.setText(path)
            self._update_preview()

    def _update_preview(self):
        """Refresh the path preview tree based on current selection and settings."""
        self.preview_tree.clear()
        export_path  = self.field_export_path.text().strip()
        preset_name  = self.combo_preset.currentData()
        one_per_file = self.cb_one_file_each.isChecked()
        use_subfolder = self.cb_use_subfolder.isChecked()

        if not export_path or not preset_name:
            return

        objects = utils.get_selected_transforms()
        if not objects and not self.cb_export_scene.isChecked():
            item = QtWidgets.QTreeWidgetItem(self.preview_tree)
            item.setText(0, "(no selection)")
            item.setText(1, "Select meshes in viewport")
            item.setForeground(0, QtGui.QColor("#666"))
            return

        exporter = FBXExporter()

        if self.cb_export_scene.isChecked():
            import maya.cmds as cmds
            scene_name = cmds.file(q=True, sceneName=True, shortName=True)
            scene_name = os.path.splitext(scene_name)[0] if scene_name else "untitled_scene"
            dest = os.path.join(export_path, preset_name).replace("\\", "/") if use_subfolder else export_path
            pairs = [(scene_name, os.path.join(dest, f"{scene_name}.fbx").replace("\\", "/"))]
        else:
            pairs = exporter.preview_paths(objects, export_path, preset_name,
                                           one_per_file, use_subfolder)

        for obj_name, filepath in pairs:
            item = QtWidgets.QTreeWidgetItem(self.preview_tree)
            item.setText(0, obj_name)
            item.setText(1, filepath)
            exists = os.path.exists(filepath)
            if exists and self.cb_overwrite_protect.isChecked():
                item.setForeground(1, QtGui.QColor("#f0a500"))
                item.setText(1, filepath + "  ⚠ exists")
            else:
                item.setForeground(1, QtGui.QColor("#888"))

    def _run_export(self):
        export_path = self.field_export_path.text().strip()
        if not export_path:
            QtWidgets.QMessageBox.warning(self, "No Path", "Please select an export path first.")
            return

        export_scene = self.cb_export_scene.isChecked()
        objects = utils.get_selected_transforms()

        if not export_scene and not objects:
            QtWidgets.QMessageBox.warning(self, "No Selection",
                                          "Select at least one mesh in the viewport.")
            return

        # Optional pre-validation
        if self.cb_validate_first.isChecked() and not export_scene:
            validator = AssetValidator()
            data = validator.run()
            sel_names  = {utils.short_name(o) for o in objects}
            sel_errors = [e for e in data["errors"] if e[0] in sel_names]
            if sel_errors:
                msg = "\n".join(f"  • {e[0]}: {e[1]}" for e in sel_errors[:10])
                reply = QtWidgets.QMessageBox.question(
                    self, "Validation Errors",
                    f"Found {len(sel_errors)} error(s):\n{msg}\n\nExport anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    self._set_status("Export cancelled — fix errors first")
                    return

        preset_name   = self.combo_preset.currentData()
        one_per_file  = self.cb_one_file_each.isChecked()
        use_subfolder = self.cb_use_subfolder.isChecked()
        overwrite     = self.cb_overwrite_protect.isChecked()
        scale         = self.spin_scale.value()

        def overwrite_callback(filepath):
            reply = QtWidgets.QMessageBox.question(
                self, "File Already Exists",
                f"Overwrite?\n{filepath}",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            return reply == QtWidgets.QMessageBox.Yes

        self._exporter = FBXExporter()
        results = self._exporter.export(
            objects            = objects,
            export_path        = export_path,
            preset_name        = preset_name,
            scale              = scale,
            one_file_each      = one_per_file,
            export_scene       = export_scene,
            use_subfolder      = use_subfolder,
            overwrite_protect  = overwrite,
            overwrite_callback = overwrite_callback if overwrite else None,
        )

        self._populate_export_tree(results)
        summary = self._exporter.get_summary()
        self._set_status(
            f"Export — {summary['success']}/{summary['total']} OK  |  "
            f"{summary['failed']} failed  |  {summary['skipped']} skipped"
        )
        utils.show_message(f"Export Done: {summary['success']}/{summary['total']}")
        self._update_preview()

    def _populate_export_tree(self, results):
        self.export_tree.clear()
        for r in results:
            item = QtWidgets.QTreeWidgetItem(self.export_tree)
            item.setText(0, r.object_name)
            item.setText(2, r.timestamp.split(" ")[1] if hasattr(r, "timestamp") else "")

            if r.skipped:
                item.setText(1, "⊘  Skipped (file exists)")
                item.setForeground(1, QtGui.QColor("#f0a500"))
            elif r.success:
                item.setText(1, "✔  " + os.path.basename(r.filepath))
                item.setForeground(1, QtGui.QColor("#6bcb77"))
            else:
                item.setText(1, "✖  " + r.message)
                item.setForeground(1, QtGui.QColor("#ff6b6b"))

    def _show_history(self):
        """Show full session export history in the log tree."""
        from maya_tech_system_v2.exporter.exporter import get_export_history
        history = get_export_history()
        if not history:
            self._set_status("No export history this session")
            return
        self._populate_export_tree(history)
        self._set_status(f"Showing session history — {len(history)} exports")

    def _clear_export_log(self):
        self.export_tree.clear()
        self._set_status("Export log cleared")

    # ── Report  ────

    def _export_report(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Report", "maya_tech_report.txt", "Text Files (*.txt)"
        )
        if not path:
            return

        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(path, "w", encoding="utf-8") as f:
            f.write("=== Maya Tech System — Full Report ===\n")
            f.write(f"Date: {now}\n\n")

            if self._cleaner:
                f.write("--- Cleaner ---\n")
                for k, v in self._cleaner.stats.items():
                    f.write(f"  {k}: {v}\n")
                f.write(f"  ngon_faces: {len(self._cleaner.problematic_faces)}\n\n")

            if self._validator:
                f.write("--- Validator ---\n")
                for item in self._validator.items:
                    f.write(f"  [{item.level.upper()}] {item.obj} | {item.check}: {item.message}\n")
                f.write("\n")

            if self._exporter and self._exporter.results:
                f.write("--- Exporter ---\n")
                for r in self._exporter.results:
                    status = "OK" if r.success else "FAIL"
                    f.write(f"  [{status}] {r.object_name} → {r.filepath}\n")
                    if not r.success:
                        f.write(f"         Error: {r.message}\n")

        self._set_status(f"Report saved: {path}")
        utils.show_message("Report Saved")

    # ── Helpers  ───

    def _set_status(self, msg):
        self.status_label.setText(msg)
        utils.log_info(msg)


# ── Launch helper  ─

_window_instance = None

def show():
    global _window_instance
    # Avoid opening multiple instances
    try:
        _window_instance.close()
        _window_instance.deleteLater()
    except Exception:
        pass
    _window_instance = MayaTechWindow()
    _window_instance.show()
    return _window_instance
