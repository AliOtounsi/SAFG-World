from pathlib import Path
import sys
from publish import validate
from maps import validate_maps
world=Path(sys.argv[sys.argv.index("--world")+1]) if "--world" in sys.argv else Path(".")
print("Validated",len(validate(world)),"shaders and",len(validate_maps(world)),"base submissions.")
