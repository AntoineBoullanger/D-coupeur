import json
import shutil
import subprocess
import sys
from pathlib import Path


class VideoEngineError(RuntimeError):
    pass


def _exe(name):
    """Trouve FFmpeg ou FFprobe, même dans l'application compilée."""

    executable = name if name.lower().endswith(".exe") else f"{name}.exe"

    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = base_dir / executable

        if candidate.is_file():
            return str(candidate)

    path = shutil.which(name)

    if not path:
        raise VideoEngineError(
            f"{name} est introuvable. Vérifie que FFmpeg est installé "
            "ou intégré à l'application."
        )

    return path


def _run_hidden(cmd):
    """Lance FFmpeg sans afficher de fenêtre CMD sous Windows."""

    kwargs = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }

    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    return subprocess.run(cmd, **kwargs)


def analyze_video(video_path):
    """Récupère la durée de la vidéo."""

    path = Path(video_path)

    if not path.is_file():
        raise VideoEngineError(f"Fichier introuvable : {path}")

    cmd = [
        _exe("ffprobe"),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]

    result = _run_hidden(cmd)

    if result.returncode != 0:
        raise VideoEngineError(
            result.stderr.strip() or "Analyse vidéo impossible."
        )

    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise VideoEngineError(
            "Impossible de lire la durée de la vidéo."
        ) from exc

    return {"duration": duration}


def cut_video_segment(video_path, output_path, start, duration):
    """Découpe un segment sans réencoder la vidéo."""

    source = Path(video_path)
    output = Path(output_path)

    if not source.is_file():
        raise VideoEngineError(f"Fichier vidéo introuvable : {source}")

    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        _exe("ffmpeg"),
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-ss", f"{max(0.0, start):.3f}",
        "-i", str(source),
        "-t", f"{duration:.3f}",
        "-map", "0",
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output),
    ]

    result = _run_hidden(cmd)

    if result.returncode != 0:
        output.unlink(missing_ok=True)
        raise VideoEngineError(
            result.stderr.strip() or f"Échec de découpe : {output.name}"
        )