"""Tests for transcript parser."""
import pytest
from pathlib import Path

from src.engines import TranscriptParser, TranscriptParsingError


def test_parser_valid_episode():
    """Test parsing a valid episode file."""
    parser = TranscriptParser()
    episode_path = Path("sample_inputs/ep001_remote_work.json")

    episode = parser.parse_file(episode_path)

    assert episode.episode_id == "ep001"
    assert episode.title == "The Future of Remote Work"
    assert episode.host == "Sarah Johnson"
    assert len(episode.transcript) == 19
    assert episode.word_count > 0
    assert episode.section_count > 0


def test_parser_all_sample_episodes():
    """Test parsing all sample episodes."""
    parser = TranscriptParser()
    sample_dir = Path("sample_inputs")
    episode_files = sorted(sample_dir.glob("*.json"))

    assert len(episode_files) == 3

    episodes = parser.parse_multiple(episode_files)

    assert len(episodes) == 3
    assert len(parser.errors) == 0

    # Verify each episode
    assert episodes[0].episode_id == "ep001"
    assert episodes[1].episode_id == "ep002"
    assert episodes[2].episode_id == "ep003"


def test_parser_validation_report():
    """Test validation report generation."""
    parser = TranscriptParser()
    episode_path = Path("sample_inputs/ep001_remote_work.json")

    episode = parser.parse_file(episode_path)
    report = parser.get_validation_report(episode)

    assert report["episode_id"] == "ep001"
    assert report["validation_status"] == "passed"
    assert report["segment_count"] == 19
    assert "Sarah" in report["speakers"]
    assert "Introduction" in report["sections"]


def test_parser_missing_file():
    """Test error handling for missing file."""
    parser = TranscriptParser()

    with pytest.raises(TranscriptParsingError) as exc_info:
        parser.parse_file(Path("nonexistent.json"))

    assert "not found" in str(exc_info.value).lower()


def test_parser_invalid_json():
    """Test error handling for invalid JSON."""
    parser = TranscriptParser()

    # Create temporary invalid JSON file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json")
        temp_path = Path(f.name)

    try:
        with pytest.raises(TranscriptParsingError) as exc_info:
            parser.parse_file(temp_path)

        assert "invalid json" in str(exc_info.value).lower()
    finally:
        temp_path.unlink()


def test_episode_methods():
    """Test episode helper methods."""
    parser = TranscriptParser()
    episode = parser.parse_file(Path("sample_inputs/ep001_remote_work.json"))

    # Test get_sections
    sections = episode.get_sections()
    assert "Introduction" in sections
    assert "Closing" in sections

    # Test get_speakers
    speakers = episode.get_speakers()
    assert "Sarah" in speakers
    assert "Mark" in speakers

    # Test get_full_text
    full_text = episode.get_full_text()
    assert len(full_text) > 0
    assert "remote" in full_text.lower()

    # Test get_text_by_section
    intro_text = episode.get_text_by_section("Introduction")
    assert len(intro_text) > 0
