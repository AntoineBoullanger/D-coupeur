from pathlib import Path
import re
from src.video_engine import cut_video_segment


def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name).strip().rstrip(". ")
    return name or "video"


def export_clips(
    video_path,
    output_folder,
    segments,
    video_name=None,
    progress_callback=None
):
    source = Path(video_path)
    folder = Path(output_folder)

    # Nom de la vidéo originale sans extension
    base = safe_filename(video_name or source.stem)

    # Créer un sous-dossier portant le nom de la vidéo originale
    folder = folder / base
    folder.mkdir(parents=True, exist_ok=True)

    outputs = []
    total = len(segments)

    for pos, segment in enumerate(segments, 1):
        target = folder / f"Partie {segment.index} -- {base}.mp4"

        suffix = 2
        while target.exists():
            target = folder / f"Partie {segment.index} -- {base} ({suffix}).mp4"
            suffix += 1

        cut_video_segment(
            source,
            target,
            segment.start,
            segment.duration
        )

        outputs.append(target)

        if progress_callback:
            progress_callback(pos, total, target.name)

    return outputs