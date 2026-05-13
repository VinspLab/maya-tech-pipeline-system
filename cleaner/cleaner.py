"""
cleaner/cleaner.py
------------------
Cleans Maya scenes before export:
  - Delete construction history
  - Freeze transforms
  - Delete unused nodes
  - Delete empty groups
  - Rename meshes with prefix/suffix/base name
  - Detect and fix n-gons
"""

import datetime
import maya.cmds as cmds
import maya.mel as mel

from maya_tech_system_v2.core import utils


class SceneCleaner:

    def __init__(self):
        self.stats = {
            "history":      0,
            "frozen":       0,
            "empty_groups": 0,
            "renamed":      0,
        }
        self.problematic_meshes = []
        self.problematic_faces  = []

    # ── Run  ──

    def run(self, prefix="", suffix="", base_name="",
            delete_history=True, freeze_transforms=True,
            delete_unused=True, delete_empty_groups=True,
            fix_ngons=False, fix_pivots=False, fix_naming=False):
        """Run all cleaning steps and return report data."""

        if delete_history:
            self.delete_history()

        if freeze_transforms:
            self.freeze_transforms()

        if delete_unused:
            self.delete_unused_nodes()

        if delete_empty_groups:
            self.delete_empty_groups()

        if fix_ngons:
            self.detect_ngons()
            if self.problematic_faces:
                self.fix_ngons()

        if fix_pivots:
            self.fix_pivots()

        if prefix or suffix or base_name or fix_naming:
            self.rename_meshes(prefix, suffix, base_name)

        self.detect_ngons()

        return self.get_report_data()

    # Steps  

    def delete_history(self):
        meshes = utils.get_transforms_from_shapes(utils.get_all_meshes())
        if meshes:
            cmds.delete(meshes, constructionHistory=True)
        self.stats["history"] = len(meshes)
        utils.log_info(f"History deleted on {len(meshes)} objects")

    def freeze_transforms(self):
        meshes = utils.get_transforms_from_shapes(utils.get_all_meshes())
        count = 0
        for obj in meshes:
            try:
                cmds.makeIdentity(obj, apply=True, t=1, r=1, s=1)
                count += 1
            except Exception as e:
                utils.log_warning(f"Could not freeze {utils.short_name(obj)}: {e}")
        self.stats["frozen"] = count
        utils.log_info(f"Transforms frozen on {count} objects")

    def delete_unused_nodes(self):
        try:
            mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
            utils.log_info("Unused nodes deleted")
        except Exception as e:
            utils.log_warning(f"Could not delete unused nodes: {e}")

    def delete_empty_groups(self):
        transforms = cmds.ls(type='transform', long=True) or []
        count = 0
        # Sort by depth (deepest first) to safely delete nested empties
        transforms.sort(key=lambda x: x.count("|"), reverse=True)
        for obj in transforms:
            if not cmds.listRelatives(obj, children=True, fullPath=True):
                try:
                    cmds.delete(obj)
                    count += 1
                except Exception as e:
                    utils.log_warning(f"Could not delete {utils.short_name(obj)}: {e}")
        self.stats["empty_groups"] = count
        utils.log_info(f"Deleted {count} empty groups")

    # Rename

    def rename_meshes(self, prefix="", suffix="", base_name=""):
        """
        Rename all meshes.

        Naming pattern:  [prefix_]<base_name|original_name>_[suffix_]<number>

        Rules:
          - Number is 1, 2, 3 (no zero-padding)
          - If no base_name, keep the mesh's current short name (strip any
            trailing digits so we don't accumulate numbers on repeated runs)
          - prefix and suffix are joined with _ only when present
          - Strategy: temp rename first to avoid name conflicts, then final name

        Examples (prefix=SM, suffix=UI, base_name=Rock):
          SM_Rock_UI_1, SM_Rock_UI_2

        Examples (prefix=SM, suffix=UI, base_name=""):
          SM_Barrel_UI_1, SM_Crate_UI_2   (original names kept)
        """
        meshes = utils.get_transforms_from_shapes(utils.get_all_meshes())
        if not meshes:
            return

        # Store original short names BEFORE any renaming
        original_names = [utils.short_name(obj) for obj in meshes]

        # Pass 1 — temp names to avoid conflicts
        temp_names = []
        for i, obj in enumerate(meshes):
            temp = f"__temp_mesh_{i}__"
            try:
                result = cmds.rename(obj, temp)
                temp_names.append(result)
            except Exception as e:
                utils.log_warning(f"Temp rename failed for index {i}: {e}")
                temp_names.append(obj)

        # Pass 2 — build and apply final names
        count = 0
        for i, obj in enumerate(temp_names):
            number = str(i + 1)   # 1, 2, 3 — no padding

            # Decide the base: explicit base_name or strip trailing digits from original
            if base_name:
                core = base_name
            else:
                # Remove trailing underscore+digits from previous runs  e.g. "Barrel_UI_1" → "Barrel"
                import re
                core = re.sub(r'(_[A-Za-z]+)?_\d+$', '', original_names[i])
                # Also strip any leading prefix that matches current prefix to avoid duplication
                if prefix and core.startswith(prefix + "_"):
                    core = core[len(prefix) + 1:]

            # Assemble parts — only join non-empty strings
            parts = []
            if prefix:
                parts.append(prefix)
            parts.append(core)
            if suffix:
                parts.append(suffix)
            parts.append(number)

            final_name = "_".join(parts)

            try:
                cmds.rename(obj, final_name)
                count += 1
            except Exception as e:
                utils.log_warning(f"Final rename failed for {obj}: {e}")

        self.stats["renamed"] = count
        utils.log_info(f"Renamed {count} meshes")

    def fix_pivots(self):
        """Move the rotate/scale pivot of all meshes to world origin."""
        meshes = utils.get_transforms_from_shapes(utils.get_all_meshes())
        count = 0
        for obj in meshes:
            try:
                cmds.xform(obj, worldSpace=True, pivots=[0, 0, 0])
                count += 1
            except Exception as e:
                utils.log_warning(f"Could not fix pivot for {utils.short_name(obj)}: {e}")
        self.stats["pivots_fixed"] = count
        utils.log_info(f"Pivots moved to origin on {count} objects")

    def fix_naming(self, prefix="", suffix=""):
        """
        Add prefix/suffix to meshes that don't already have them,
        without touching the base name.
        """
        meshes = utils.get_transforms_from_shapes(utils.get_all_meshes())
        count = 0
        temp_names = []

        # Pass 1 — temp rename to avoid conflicts
        for i, obj in enumerate(meshes):
            temp = f"__temp_fixname_{i}__"
            try:
                result = cmds.rename(obj, temp)
                temp_names.append((result, utils.short_name(obj)))
            except Exception as e:
                utils.log_warning(f"Temp rename failed: {e}")
                temp_names.append((obj, utils.short_name(obj)))

        # Pass 2 — apply prefix/suffix only if missing
        for temp_obj, original in temp_names:
            name = original
            if prefix and not name.startswith(prefix + "_"):
                name = f"{prefix}_{name}"
            if suffix and not name.endswith("_" + suffix):
                name = f"{name}_{suffix}"
            try:
                cmds.rename(temp_obj, name)
                count += 1
            except Exception as e:
                utils.log_warning(f"Fix naming failed for {original}: {e}")

        utils.log_info(f"Fix naming applied to {count} meshes")

    # N-gon Detection / Fix

    def detect_ngons(self):
        """Detect faces with more than 4 vertices on all meshes."""
        self.problematic_faces  = []
        self.problematic_meshes = []

        for mesh in utils.get_all_meshes():
            transform = cmds.listRelatives(mesh, parent=True, fullPath=True)
            if not transform:
                continue
            transform = transform[0]

            info = cmds.polyInfo(mesh, faceToVertex=True) or []
            ngon_found = False

            for line in info:
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                face_id = parts[0].split()[-1]
                verts   = parts[1].strip().split()

                if len(verts) > 4:
                    self.problematic_faces.append(f"{transform}.f[{face_id}]")
                    ngon_found = True

            if ngon_found and transform not in self.problematic_meshes:
                self.problematic_meshes.append(transform)

        utils.log_info(f"N-gon detection: {len(self.problematic_faces)} faces on "
                       f"{len(self.problematic_meshes)} meshes")

    def fix_ngons(self):
        """
        Fix n-gon faces: try quadrangulate first (preserves quads),
        then triangulate any remaining n-gons as fallback.
        """
        if not self.problematic_faces:
            self.detect_ngons()

        if not self.problematic_faces:
            utils.log_info("No n-gons to fix")
            return 0

        total = len(self.problematic_faces)

        # Pass 1 — quadrangulate the problem meshes
        try:
            cmds.select(self.problematic_meshes)
            cmds.polyQuad(angle=180, keepGroupBorder=1, worldSpace=0)
            utils.log_info("Quadrangulate pass done")
        except Exception as e:
            utils.log_warning(f"Quadrangulate pass failed: {e}")
        cmds.select(clear=True)

        # Pass 2 — re-detect; triangulate whatever remains
        self.detect_ngons()
        if self.problematic_faces:
            try:
                cmds.polyTriangulate(self.problematic_faces)
                utils.log_info(f"Triangulated {len(self.problematic_faces)} remaining faces")
            except Exception as e:
                utils.log_error(f"Triangulate pass failed: {e}")
        cmds.select(clear=True)

        # Final state update
        self.detect_ngons()
        utils.log_info(f"Fix NGons done — {len(self.problematic_faces)} remaining")
        return total

    # Report

    def get_report_data(self):
        return {
            "stats":          self.stats,
            "ngon_faces":     self.problematic_faces,
            "problem_meshes": self.problematic_meshes,
        }

    def export_report(self, path):
        path = path.replace("\\", "/")
        now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(path, "w", encoding="utf-8") as f:
            f.write("=== Maya Tech System — Cleaner Report ===\n")
            f.write(f"Date: {now}\n\n")

            f.write("--- Stats ---\n")
            for k, v in self.stats.items():
                f.write(f"  {k}: {v}\n")

            f.write("\n--- N-gon Faces ---\n")
            for face in self.problematic_faces:
                f.write(f"  {face}\n")

        return path