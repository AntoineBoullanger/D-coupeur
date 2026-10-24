import json
import shutil
import subprocess
from pathlib import Path


class VideoEngineError(RuntimeError):
    pass


def _exe(name):
    path = shutil.which(name)

    if not path:
        raise VideoEngineError(
            f"{name} est introuvable. Installe FFmpeg et ajoute-le au PATH."
        )

    return path


def _run_hidden(cmd):
    """Exécute une commande sans afficher de fenêtre CMD sous Windows."""
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

    if result.returncode:
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

    if result.returncode:
        output.unlink(missing_ok=True)
        raise VideoEngineError(
            result.stderr.strip() or f"Échec de découpe : {output.name}"
        )