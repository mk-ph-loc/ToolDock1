"""Launcher χωρίς κονσόλα (για συντομεύσεις): προσθέτει το src στο sys.path."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from tooldock.app import main  # noqa: E402

sys.exit(main())
