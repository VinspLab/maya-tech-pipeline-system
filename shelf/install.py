"""
shelf/install.py
----------------
Creates a shelf button in Maya that launches Maya Tech System.

Run once inside Maya's Script Editor:

    import sys
    sys.path.insert(0, "C:/path/to/your/tools")

    from maya_tech_system_v2.shelf import install
    install.create_shelf_button()
"""

import maya.cmds as cmds
import maya.mel as mel


TOOL_PATH_PLACEHOLDER = "C:/path/to/your/tools"   # ← change before running

SHELF_SCRIPT = f"""
import sys
if "{TOOL_PATH_PLACEHOLDER}" not in sys.path:
    sys.path.insert(0, "{TOOL_PATH_PLACEHOLDER}")
from maya_tech_system_v2 import main
main.show()
"""

SHELF_NAME   = "Custom"
BUTTON_LABEL = "MTS"
BUTTON_TOOLTIP = "Maya Tech System — Cleaner · Validator · Exporter"


def create_shelf_button(shelf_name=SHELF_NAME):
    """Add a shelf button that opens Maya Tech System."""
    # Make sure the target shelf exists
    if not cmds.shelfLayout(shelf_name, exists=True):
        mel.eval(f'addNewShelfTab "{shelf_name}"')

    cmds.shelfButton(
        parent      = shelf_name,
        label       = BUTTON_LABEL,
        annotation  = BUTTON_TOOLTIP,
        command     = SHELF_SCRIPT,
        sourceType  = "python",
        imageOverlayLabel = BUTTON_LABEL,
        image1      = "pythonFamily.png",   # built-in Maya icon
        overlayLabelColor = (1, 0.75, 0),   # amber
    )

    print(f"[MayaTech] Shelf button created on shelf '{shelf_name}'")
