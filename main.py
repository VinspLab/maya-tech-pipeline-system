"""
main.py
-------
Entry point for Maya Tech System.

Run inside Maya's Script Editor (Python tab):

    import importlib, sys

    # First time:
    sys.path.insert(0, "C:/path/to/your/tools")   # folder that CONTAINS maya_tech_system_v2
    from maya_tech_system_v2 import main
    main.show()

    # After code changes — reload everything:
    main.reload_all()
    main.show()
"""

def show():
    from maya_tech_system_v2.ui.main_window import show as _show
    return _show()


def reload_all():
    """Force-reload all modules (useful during development)."""
    import importlib, sys

    modules_to_reload = [
        "maya_tech_system_v2.core.utils",
        "maya_tech_system_v2.exporter.config",
        "maya_tech_system_v2.exporter.exporter",
        "maya_tech_system_v2.cleaner.cleaner",
        "maya_tech_system_v2.validator.validator",
        "maya_tech_system_v2.ui.main_window",
        "maya_tech_system_v2.main",
    ]

    for mod_name in modules_to_reload:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

    print("[MayaTech] All modules reloaded.")
