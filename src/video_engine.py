import json, shutil, subprocess
from pathlib import Path

class VideoEngineError(RuntimeError):
    pass

def _exe(name):
    path = shutil.which(name)
    if not path:
        raise VideoEngineError(f"{name} est introuvable. Installe FFmpeg et ajoute-le au PATH.")
    return path

def analyze_video(video_path):
    path = Path(video_path)
    if not path.is_file():
        raise VideoEngineError(f"Fichier introuvable : {path}")
    cmd = [_exe("ffprobe"), "-v", "error", "-show_entries", "format=duration",
           "-of", "json", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise VideoEngineError(result.stderr.strip() or "Analyse vidéo impossible.")
    return {"duration": float(json.loads(result.stdout)["format"]["duration"])}

def cut_video_segment(video_path, output_path, start, duration):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [_exe("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
           "-ss", f"{max(0.0, start):.3f}", "-i", str(video_path),
           "-t", f"{duration:.3f}", "-map", "0", "-c", "copy",
           "-avoid_negative_ts", "make_zero", str(output)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        output.unlink(missing_ok=True)
        raise VideoEngineError(result.stderr.strip() or f"Échec de découpe : {output.name}")
