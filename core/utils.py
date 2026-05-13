import maya.cmds as cmds
import logging

logger = logging.getLogger("MayaTechSystem")


def get_all_meshes():
    """Return all mesh shapes in the scene (long paths)."""
    return cmds.ls(type='mesh', long=True) or []


def get_transforms_from_shapes(shapes):
    """Return unique transform nodes from a list of shape nodes."""
    transforms = []
    for shape in shapes:
        parent = cmds.listRelatives(shape, parent=True, fullPath=True)
        if parent:
            transforms.append(parent[0])
    return list(set(transforms))


def get_selected_transforms():
    """Return selected transform nodes that have mesh shapes."""
    selection = cmds.ls(selection=True, long=True) or []
    result = []
    for obj in selection:
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh', fullPath=True)
        if shapes:
            result.append(obj)
    return result


def short_name(full_path):
    """Return the short name from a full DAG path."""
    return full_path.split("|")[-1]


def show_message(message, position="topCenter"):
    """Show an in-viewport HUD message."""
    try:
        cmds.inViewMessage(amg=f"<b>[MayaTech]</b> {message}", pos=position, fade=True)
    except Exception:
        pass


def log_info(message):
    logger.info(message)
    print(f"[MayaTech] {message}")


def log_warning(message):
    logger.warning(message)
    print(f"[MayaTech][WARNING] {message}")


def log_error(message):
    logger.error(message)
    print(f"[MayaTech][ERROR] {message}")
