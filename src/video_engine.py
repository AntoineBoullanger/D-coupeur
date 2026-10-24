import json
import shutil
import subprocess
import sys
from pathlib import Path


class VideoEngineError(RuntimeError):
    pass


def _exe(name):
    # Chercher les exécutables intégrés à l'application
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)
        extensions = [".exe", ""] if not name.lower().endswith(".exe") else [""]
        for ext in extensions:
            candidate = base_dir / f"{name}{ext}"
            if candidate.is_file():
                return str(candidate)

    # Sinon, chercher FFmpeg sur le PC
    path = shutil.which(name)

    if not path:
        raise VideoEngineError(
            f"{name} est introuvable. Vérifie que FFmpeg est intégré à l'application."
        )

    return path