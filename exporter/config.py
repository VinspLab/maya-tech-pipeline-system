"""
exporter/config.py
------------------
Centralized configuration for FBX export presets.
Each preset maps to a specific Unreal asset type.
"""

# ── Asset type prefixes (Unreal Engine convention) ──────────────────────────
UNREAL_PREFIXES = {
    "SM":  "SM_",   # Static Mesh
    "SK":  "SK_",   # Skeletal Mesh
    "T":   "T_",    # Texture
    "MI":  "MI_",   # Material Instance
    "BP":  "BP_",   # Blueprint
}

# ── FBX Export Presets ───────────────────────────────────────────────────────
# Each key is a preset name shown in the UI.
# Values map directly to Maya FBX export commands.

FBX_PRESETS = {

    "StaticMesh": {
        "description": "Static Mesh for Unreal Engine",
        "triangulate":        True,
        "smoothing_groups":   True,
        "hard_edges":         False,
        "tangents":           True,
        "smooth_mesh":        False,
        "instances":          False,
        "referenced_assets":  False,
        "animation":          False,
        "cameras":            False,
        "lights":             False,
        "embed_textures":     False,
        "bake_animation":     False,
        "axis_conversion":    True,    # Y-up (Maya) → Z-up (Unreal)
        "file_version":       "FBX202000",
    },

    "SkeletalMesh": {
        "description": "Skeletal Mesh with skeleton for Unreal Engine",
        "triangulate":        True,
        "smoothing_groups":   True,
        "hard_edges":         False,
        "tangents":           True,
        "smooth_mesh":        False,
        "instances":          False,
        "referenced_assets":  False,
        "animation":          False,   # export separately
        "cameras":            False,
        "lights":             False,
        "embed_textures":     False,
        "bake_animation":     False,
        "axis_conversion":    True,
        "file_version":       "FBX202000",
        "skins":              True,
        "shapes":             True,    # blend shapes / morph targets
    },

    "Animation": {
        "description": "Animation clip for Unreal Engine",
        "triangulate":        False,
        "smoothing_groups":   False,
        "hard_edges":         False,
        "tangents":           False,
        "smooth_mesh":        False,
        "instances":          False,
        "referenced_assets":  False,
        "animation":          True,
        "cameras":            False,
        "lights":             False,
        "embed_textures":     False,
        "bake_animation":     True,
        "bake_start":         1,
        "bake_end":           100,
        "bake_step":          1,
        "axis_conversion":    True,
        "file_version":       "FBX202000",
        "skins":              True,
        "shapes":             True,
    },
}

# ── Default export path (can be overridden per session) ─────────────────────
DEFAULT_EXPORT_PATH = ""

# ── Naming convention ────────────────────────────────────────────────────────
VALID_PREFIXES = ("SM_", "SK_", "T_", "MI_", "BP_", "geo_")
