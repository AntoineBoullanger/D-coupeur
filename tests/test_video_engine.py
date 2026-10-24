import pytest

from src.video_engine import VideoEngineError, analyze_video
from src.clip_splitter import split_video_timeline


def test_analyze_video_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "video_inexistante.mp4"

    with pytest.raises(
        VideoEngineError,
        match="n'existe pas",
    ):
        analyze_video(missing_file)


def test_segments_cover_entire_video():
    segments = split_video_timeline(
        total_duration=125,
        min_duration=30,
        max_duration=60,
        seed=42,
    )

    assert segments[0].start == 0
    assert segments[-1].end == pytest.approx(125)

    for previous, current in zip(segments, segments[1:]):
        assert previous.end == pytest.approx(current.start)


def test_fixed_duration():
    segments = split_video_timeline(
        total_duration=100,
        fixed_duration=30,
    )

    assert [segment.duration for segment in segments] == [
        30,
        30,
        30,
        10,
    ]


def test_short_video_produces_one_segment():
    segments = split_video_timeline(
        total_duration=15,
        min_duration=30,
        max_duration=60,
    )

    assert len(segments) == 1
    assert segments[0].duration == pytest.approx(15)


def test_invalid_durations_are_rejected():
    with pytest.raises(VideoEngineError):
        split_video_timeline(
            total_duration=100,
            min_duration=60,
            max_duration=30,
        )
        
        
from src.clip_exporter import safe_filename


def test_safe_filename():
    assert safe_filename("Ma vidéo: test") == "Ma vidéo_ test"
    assert safe_filename("") == "video"
    
def test_segments_have_overlap():
    segments = split_video_timeline(
        180,
        min_duration=30,
        max_duration=60,
        overlap=5,
        seed=42,
    )

    assert segments[0].start == 0

    for previous, current in zip(segments, segments[1:]):
        assert abs((previous.end - current.start) - 5) < 0.001


def test_segments_reach_end_of_video():
    total_duration = 180

    segments = split_video_timeline(
        total_duration,
        min_duration=30,
        max_duration=60,
        overlap=5,
        seed=42,
    )

    assert abs(segments[-1].end - total_duration) < 0.001


def test_overlap_must_be_less_than_minimum_duration():
    with pytest.raises(VideoEngineError):
        split_video_timeline(
            180,
            min_duration=10,
            max_duration=30,
            overlap=10,
        )