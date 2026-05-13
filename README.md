# Maya Tech System

Pipeline tool for Maya → Unreal Engine export.  
Built for production AAA/AA workflows.



## Features

|Module|What it does|
|-|-|
|**Cleaner**|Delete history, freeze transforms, remove unused nodes/empty groups, rename meshes|
|**Validator**|Check n-gons, non-manifold geo, naming convention, pivot position, history|
|**Exporter**|Export FBX to Unreal Content folder with correct axis, triangulation and presets|



## Project Structure


maya\_tech\_system\_v2/
├── core/
│   └── utils.py          # Shared helpers (no UI, no business logic)
├── cleaner/
│   └── cleaner.py        # SceneCleaner class
├── validator/
│   └── validator.py      # AssetValidator class
├── exporter/
│   ├── config.py         # FBX presets \& naming conventions
│   └── exporter.py       # FBXExporter class
├── ui/
│   └── main\_window.py    # PySide2 window (3 tabs)
├── shelf/
│   └── install.py        # One-time shelf button installer
└── main.py               # Entry point: main.show()




## Quick Start

1. Copy the `maya\_tech\_system\_v2` folder somewhere on disk.
2. Open Maya's **Script Editor** (Python tab) and run:

```python
import sys
sys.path.insert(0, "C:/path/to/your/tools")   # folder containing maya\_tech\_system\_v2

from maya\_tech\_system\_v2 import main
main.show()
```

3. (Optional) Install a shelf button:

```python
from maya\_tech\_system\_v2.shelf import install
install.create\_shelf\_button()
```



## Workflow


1. Open scene in Maya
2. Cleaner tab  → Run Cleaner   (clean history, freeze, rename)
3. Validator tab → Run Validator (check for errors/warnings)
4. Validator tab → Fix All       (auto-fix what can be fixed)
5. Exporter tab  → Set path, choose preset, select meshes → Export




## FBX Presets

|Preset|Use for|
|-|-|
|`StaticMesh`|Props, environment pieces, architecture|
|`SkeletalMesh`|Characters, creatures (with skeleton)|
|`Animation`|Animation clips (baked, no mesh needed)|



## Naming Convention (Unreal)

|Prefix|Asset type|
|-|-|
|`SM\_`|Static Mesh|
|`SK\_`|Skeletal Mesh|
|`T\_`|Texture|
|`MI\_`|Material Instance|
|`BP\_`|Blueprint|



## Reloading during development

```python
from maya\_tech\_system\_v2 import main
main.reload\_all()
main.show()
```

