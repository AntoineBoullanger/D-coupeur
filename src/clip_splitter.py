from dataclasses import dataclass
import random

@dataclass(frozen=True)
class ClipSegment:
    index: int
    start: float
    end: float
    @property
    def duration(self):
        return max(0.0, self.end - self.start)

def split_video_timeline(total_duration, min_duration=30, max_duration=60, overlap=0, seed=None):
    if total_duration <= 0:
        raise ValueError("La durée de la vidéo doit être positive.")
    if min_duration <= 0 or max_duration < min_duration:
        raise ValueError("Les durées minimale et maximale sont invalides.")
    if overlap < 0 or overlap >= min_duration:
        raise ValueError("Le chevauchement doit être positif et inférieur à la durée minimale.")
    rng = random.Random(seed)
    segments, start, index = [], 0.0, 1
    while start < total_duration - 0.05:
        remaining = total_duration - start
        chosen = rng.randint(int(min_duration), int(max_duration))
        end = total_duration if remaining <= chosen else min(start + chosen, total_duration)
        if end <= start:
            break
        segments.append(ClipSegment(index, start, end))
        if end >= total_duration:
            break
        start = end - overlap
        index += 1
    return segments
