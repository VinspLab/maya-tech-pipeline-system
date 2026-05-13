"""
exporter/exporter.py
--------------------
Handles FBX export from Maya to an Unreal Engine content folder.
Applies the correct preset per asset type and validates the mesh
before exporting.

Options
-------
  scale            : float — export scale factor (default 1.0; use 100 for Maya→UE unit fix)
  one_file_each    : bool  — one FBX per object vs. batch into one file
  export_scene     : bool  — export whole scene instead of selection
  use_subfolder    : bool  — create subfolder per preset type (StaticMesh/, SkeletalMesh/, etc.)
  overwrite_protect: bool  — warn before overwriting existing files
"""

import os
import datetime
import maya.cmds as cmds
import maya.mel as mel

from maya_tech_system_v2.core import utils
from maya_tech_system_v2.exporter.config import FBX_PRESETS


class ExportResult:
    """Holds the outcome of a single export operation."""

    def __init__(self, object_name, filepath, success, message="", skipped=False):
        self.object_name = object_name
        self.filepath    = filepath
        self.success     = success
        self.message     = message
        self.skipped     = skipped      # True when overwrite was blocked
        self.timestamp   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self):
        if self.skipped:
            status = "SKIP"
        else:
            status = "OK" if self.success else "FAIL"
        return f"[{status}] {self.object_name} → {self.filepath} | {self.message}"


# Session-level export history (persists while Maya is open)
_export_history = []   # list[ExportResult]


def get_export_history():
    return list(_export_history)


def clear_export_history():
    global _export_history
    _export_history = []


class FBXExporter:
    """
    Exports meshes to FBX with configurable options.

    Usage
    -----
    exporter = FBXExporter()
    results  = exporter.export(
        objects           = ["SM_Rock_001"],
        export_path       = "C:/UE5Project/Content/Environment",
        preset_name       = "StaticMesh",
        scale             = 1.0,
        one_file_each     = True,
        export_scene      = False,
        use_subfolder     = True,
        overwrite_protect = True,
    )
    """

    def __init__(self):
        self.results = []

    # Public

    def export(self, objects, export_path, preset_name="StaticMesh",
               scale=1.0, one_file_each=True, export_scene=False,
               use_subfolder=False, overwrite_protect=True,
               overwrite_callback=None):
        """
        Export meshes to FBX.

        Parameters
        ----------
        objects           : list[str]  — transform nodes to export
        export_path       : str        — base destination folder
        preset_name       : str        — key in FBX_PRESETS
        scale             : float      — export scale (1.0 = no change, 100.0 = cm→m fix)
        one_file_each     : bool       — one FBX per object vs. batch
        export_scene      : bool       — ignore objects list and export whole scene
        use_subfolder     : bool       — create preset-named subfolder automatically
        overwrite_protect : bool       — skip files that already exist (callback decides)
        overwrite_callback: callable   — fn(filepath) → bool: True = proceed, False = skip
                                         used by UI to show a dialog
        """
        self.results = []

        preset = FBX_PRESETS.get(preset_name)
        if not preset:
            utils.log_error(f"Unknown preset: {preset_name}")
            return self.results

        # Resolve final export folder
        dest = export_path
        if use_subfolder:
            dest = os.path.join(export_path, preset_name).replace("\\", "/")

        if not os.path.isdir(dest):
            try:
                os.makedirs(dest)
                utils.log_info(f"Created export directory: {dest}")
            except OSError as e:
                utils.log_error(f"Cannot create export directory: {e}")
                return self.results

        self._apply_fbx_settings(preset, scale)

        if export_scene:
            self._export_scene(dest, preset_name, overwrite_protect, overwrite_callback)
        elif one_file_each:
            for obj in objects:
                self._export_single(obj, dest, preset_name,
                                    overwrite_protect, overwrite_callback)
        else:
            self._export_batch(objects, dest, preset_name,
                               overwrite_protect, overwrite_callback)

        # Append to session history
        global _export_history
        _export_history.extend(self.results)

        return self.results

    def preview_paths(self, objects, export_path, preset_name,
                      one_file_each=True, use_subfolder=False):
        """
        Return a list of (object_name, filepath) without exporting.
        Used by the UI preview panel.
        """
        dest = export_path
        if use_subfolder:
            dest = os.path.join(export_path, preset_name).replace("\\", "/")

        if one_file_each:
            return [(utils.short_name(o),
                     os.path.join(dest, f"{utils.short_name(o)}.fbx").replace("\\", "/"))
                    for o in objects]
        else:
            batch_path = os.path.join(dest, f"batch_export_{preset_name}.fbx").replace("\\", "/")
            return [(utils.short_name(o), batch_path) for o in objects]

    # Private

    def _export_single(self, obj, dest, preset_name, overwrite_protect, overwrite_callback):
        short    = utils.short_name(obj)
        filepath = os.path.join(dest, f"{short}.fbx").replace("\\", "/")

        if overwrite_protect and os.path.exists(filepath):
            proceed = overwrite_callback(filepath) if overwrite_callback else False
            if not proceed:
                result = ExportResult(short, filepath, False,
                                      "Skipped — file exists", skipped=True)
                self.results.append(result)
                utils.log_warning(f"Skipped (overwrite): {filepath}")
                return

        original = cmds.ls(selection=True, long=True)
        try:
            cmds.select(obj, replace=True)
            cmds.file(filepath, force=True, options="v=0",
                      type="FBX export", preserveReferences=True, exportSelected=True)
            self.results.append(ExportResult(short, filepath, True, "Exported successfully"))
            utils.log_info(f"Exported: {short} → {filepath}")
        except Exception as e:
            self.results.append(ExportResult(short, filepath, False, str(e)))
            utils.log_error(f"Failed to export {short}: {e}")
        finally:
            cmds.select(original, replace=True) if original else cmds.select(clear=True)

    def _export_batch(self, objects, dest, preset_name, overwrite_protect, overwrite_callback):
        filepath = os.path.join(dest, f"batch_export_{preset_name}.fbx").replace("\\", "/")

        if overwrite_protect and os.path.exists(filepath):
            proceed = overwrite_callback(filepath) if overwrite_callback else False
            if not proceed:
                for obj in objects:
                    self.results.append(
                        ExportResult(utils.short_name(obj), filepath,
                                     False, "Skipped — file exists", skipped=True))
                return

        original = cmds.ls(selection=True, long=True)
        try:
            cmds.select(objects, replace=True)
            cmds.file(filepath, force=True, options="v=0",
                      type="FBX export", preserveReferences=True, exportSelected=True)
            for obj in objects:
                self.results.append(
                    ExportResult(utils.short_name(obj), filepath, True, "Batch export"))
        except Exception as e:
            for obj in objects:
                self.results.append(
                    ExportResult(utils.short_name(obj), filepath, False, str(e)))
            utils.log_error(f"Batch export failed: {e}")
        finally:
            cmds.select(original, replace=True) if original else cmds.select(clear=True)

    def _export_scene(self, dest, preset_name, overwrite_protect, overwrite_callback):
        """Export the entire scene as a single FBX."""
        import maya.cmds as cmds
        scene_name = cmds.file(q=True, sceneName=True, shortName=True)
        scene_name = os.path.splitext(scene_name)[0] if scene_name else "untitled_scene"
        filepath   = os.path.join(dest, f"{scene_name}.fbx").replace("\\", "/")

        if overwrite_protect and os.path.exists(filepath):
            proceed = overwrite_callback(filepath) if overwrite_callback else False
            if not proceed:
                self.results.append(
                    ExportResult(scene_name, filepath, False,
                                 "Skipped — file exists", skipped=True))
                return

        try:
            cmds.file(filepath, force=True, options="v=0",
                      type="FBX export", preserveReferences=True, exportAll=True)
            self.results.append(ExportResult(scene_name, filepath, True, "Scene exported"))
            utils.log_info(f"Scene exported → {filepath}")
        except Exception as e:
            self.results.append(ExportResult(scene_name, filepath, False, str(e)))
            utils.log_error(f"Scene export failed: {e}")

    def _apply_fbx_settings(self, preset, scale=1.0):
        """Apply FBX export settings via MEL commands."""
        def mel_set(cmd):
            try:
                mel.eval(cmd)
            except Exception as e:
                utils.log_warning(f"FBX setting failed: {cmd} | {e}")

        mel_set("FBXResetExport")

        # Scale factor
        mel_set(f"FBXExportScaleFactor {float(scale)}")

        # Geometry
        mel_set(f"FBXExportTriangulate -v {str(preset.get('triangulate', True)).lower()}")
        mel_set(f"FBXExportSmoothingGroups -v {str(preset.get('smoothing_groups', True)).lower()}")
        mel_set(f"FBXExportHardEdges -v {str(preset.get('hard_edges', False)).lower()}")
        mel_set(f"FBXExportTangents -v {str(preset.get('tangents', True)).lower()}")
        mel_set(f"FBXExportSmoothMesh -v {str(preset.get('smooth_mesh', False)).lower()}")
        mel_set(f"FBXExportInstances -v {str(preset.get('instances', False)).lower()}")
        mel_set(f"FBXExportReferencedAssetsContent -v {str(preset.get('referenced_assets', False)).lower()}")

        # Animation
        mel_set("FBXExportAnimationOnly -v false")
        mel_set(f"FBXExportBakeComplexAnimation -v {str(preset.get('bake_animation', False)).lower()}")
        if preset.get("bake_animation"):
            mel_set(f"FBXExportBakeComplexStart -v {preset.get('bake_start', 1)}")
            mel_set(f"FBXExportBakeComplexEnd -v {preset.get('bake_end', 100)}")
            mel_set(f"FBXExportBakeComplexStep -v {preset.get('bake_step', 1)}")

        # Scene elements
        mel_set(f"FBXExportCameras -v {str(preset.get('cameras', False)).lower()}")
        mel_set(f"FBXExportLights -v {str(preset.get('lights', False)).lower()}")
        mel_set(f"FBXExportEmbeddedTextures -v {str(preset.get('embed_textures', False)).lower()}")

        # Deformers
        if "skins" in preset:
            mel_set(f"FBXExportSkins -v {str(preset.get('skins', False)).lower()}")
        if "shapes" in preset:
            mel_set(f"FBXExportShapes -v {str(preset.get('shapes', False)).lower()}")

        # Axis / version
        mel_set("FBXExportUpAxis z")
        mel_set(f"FBXExportFileVersion -v {preset.get('file_version', 'FBX202000')}")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def get_summary(self):
        success = [r for r in self.results if r.success]
        failed  = [r for r in self.results if not r.success and not r.skipped]
        skipped = [r for r in self.results if r.skipped]
        return {
            "total":   len(self.results),
            "success": len(success),
            "failed":  len(failed),
            "skipped": len(skipped),
            "files":   [r.filepath for r in success],
            "errors":  [(r.object_name, r.message) for r in failed],
        }
