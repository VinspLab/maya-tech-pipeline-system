"""
validator/validator.py
----------------------
Validates Maya assets against Unreal Engine pipeline conventions.

Checks
------
  Errors   (must fix before export):
    - N-gons
    - Non-manifold geometry
    - Invalid naming convention

  Warnings (should fix but won't block export):
    - Construction history present
    - Pivot not at world origin
    - Empty groups in scene
"""

import maya.cmds as cmds

from maya_tech_system_v2.core import utils
from maya_tech_system_v2.exporter.config import VALID_PREFIXES


class ValidationItem:
    """A single validation result entry."""
    ERROR   = "error"
    WARNING = "warning"

    def __init__(self, level, obj, check, message):
        self.level   = level    # "error" | "warning"
        self.obj     = obj      # short object name
        self.check   = check    # check category e.g. "NGon"
        self.message = message  # human-readable detail

    def __repr__(self):
        return f"[{self.level.upper()}] {self.obj} | {self.check}: {self.message}"

    def as_tuple(self):
        return (self.obj, f"{self.check}: {self.message}")


class AssetValidator:

    def __init__(self):
        self.items    = []        # list[ValidationItem]
        self.errors   = []        # list[tuple] — kept for UI compatibility
        self.warnings = []

    # ── Run ──────────────────────────────────────────────────────────────────

    def run(self):
        """Run all checks and return structured results."""
        self.items    = []
        self.errors   = []
        self.warnings = []

        self._check_ngons()
        self._check_non_manifold()
        self._check_naming()
        self._check_history()
        self._check_pivot()
        self._check_empty_groups()

        # Populate legacy tuple lists for UI
        for item in self.items:
            if item.level == ValidationItem.ERROR:
                self.errors.append(item.as_tuple())
            else:
                self.warnings.append(item.as_tuple())

        return self.get_data()

    # ── Fix All ──────────────────────────────────────────────────────────────

    def fix_all(self, cleaner):
        """Auto-fix everything that can be fixed programmatically."""
        self.run()

        # Fix history
        meshes = utils.get_transforms_from_shapes(utils.get_all_meshes())
        if meshes:
            try:
                cmds.delete(meshes, constructionHistory=True)
            except Exception as e:
                utils.log_warning(f"History fix failed: {e}")

        # Fix pivots
        for obj in meshes:
            try:
                cmds.xform(obj, worldSpace=True, pivots=[0, 0, 0])
            except Exception as e:
                utils.log_warning(f"Pivot fix failed for {utils.short_name(obj)}: {e}")

        # Fix n-gons
        cleaner.fix_ngons()

        # Fix empty groups
        cleaner.delete_empty_groups()

        utils.log_info("Fix All completed")

    # ── Checks ───────────────────────────────────────────────────────────────

    def _check_ngons(self):
        for mesh in utils.get_all_meshes():
            transform = cmds.listRelatives(mesh, parent=True, fullPath=True)
            if not transform:
                continue
            transform = transform[0]
            short     = utils.short_name(transform)

            info = cmds.polyInfo(mesh, faceToVertex=True) or []
            for line in info:
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                verts = parts[1].strip().split()
                if len(verts) > 4:
                    self._add(ValidationItem.ERROR, short, "NGon",
                              f"Face with {len(verts)} vertices detected")
                    break   # one error per mesh is enough

    def _check_non_manifold(self):
        for mesh in utils.get_all_meshes():
            transform = cmds.listRelatives(mesh, parent=True, fullPath=True)
            if not transform:
                continue
            short = utils.short_name(transform[0])
            if cmds.polyInfo(mesh, nonManifoldEdges=True):
                self._add(ValidationItem.ERROR, short, "Non-Manifold",
                          "Non-manifold edges found — mesh is not watertight")

    def _check_naming(self):
        for transform in utils.get_transforms_from_shapes(utils.get_all_meshes()):
            short = utils.short_name(transform)
            if not any(short.startswith(p) for p in VALID_PREFIXES):
                self._add(ValidationItem.ERROR, short, "Naming",
                          f"Name must start with one of: {', '.join(VALID_PREFIXES)}")

    def _check_history(self):
        for transform in utils.get_transforms_from_shapes(utils.get_all_meshes()):
            short   = utils.short_name(transform)
            history = cmds.listHistory(transform) or []
            if len(history) > 1:
                self._add(ValidationItem.WARNING, short, "History",
                          f"{len(history)} history nodes — delete before export")

    def _check_pivot(self):
        for transform in utils.get_transforms_from_shapes(utils.get_all_meshes()):
            short = utils.short_name(transform)
            pivot = cmds.xform(transform, q=True, ws=True, rp=True) or [0, 0, 0]
            if any(abs(p) > 0.001 for p in pivot):
                self._add(ValidationItem.WARNING, short, "Pivot",
                          f"Pivot at {[round(p,3) for p in pivot]} — should be at origin")

    def _check_empty_groups(self):
        for obj in (cmds.ls(type='transform') or []):
            if not cmds.listRelatives(obj, children=True):
                self._add(ValidationItem.WARNING, obj, "Empty Group",
                          "Transform has no children")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _add(self, level, obj, check, message):
        self.items.append(ValidationItem(level, obj, check, message))

    def get_data(self):
        return {
            "errors":   self.errors,
            "warnings": self.warnings,
            "items":    self.items,
        }
