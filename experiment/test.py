### Use this boilerplat in experiment if your experiment files
### are directly inside the experiment folder (meaning not in
### subfolders)
import sys

if "../" not in sys.path:
    sys.path.insert(0, "../")
