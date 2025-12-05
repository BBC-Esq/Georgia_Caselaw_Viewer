from pathlib import Path
from PySide6.QtWidgets import QWidget
from utils.helpers import load_yaml

_TOOLTIPS = {}

def apply_tooltips(root: QWidget, section: str, actions=None):
    global _TOOLTIPS

    if not _TOOLTIPS:
        cfg_path = Path(__file__).parent.parent / "config" / "tooltips.yaml"
        _TOOLTIPS = load_yaml(cfg_path)

    tips = _TOOLTIPS.get(section, {})

    for widget in [root] + root.findChildren(QWidget):
        name = widget.objectName()
        if name and name in tips:
            widget.setToolTip(tips[name])

    if actions:
        for key, action in actions.items():
            if key in tips:
                action.setToolTip(tips[key])
                action.setStatusTip(tips[key])