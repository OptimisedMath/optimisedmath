"""Tests for curriculum YAML loading and validation."""

from pathlib import Path

import pytest

import backend.curriculum_loader as loader
from backend.problem_generation import FUNCTION_REGISTRY, get_curriculum_response


@pytest.fixture(autouse=True)
def reset_curriculum_cache():
    loader._load_curriculum_store.cache_clear()
    loader.set_function_registry(FUNCTION_REGISTRY)
    yield
    loader._load_curriculum_store.cache_clear()
    loader.set_function_registry(FUNCTION_REGISTRY)


def test_loads_real_curriculum_with_topics():
    curriculum = loader.get_curriculum()
    assert 10 in curriculum
    assert 20 in curriculum
    assert curriculum[10][0]["name"] == "Zapisywanie"


def test_chapters_ordered_by_yaml_id():
    chapters = loader.get_chapters()
    assert chapters[0].chapter_id < chapters[1].chapter_id


def test_get_chapter_yaml_uses_topics_key():
    data = loader.get_chapter_yaml(10)
    assert "topics" in data
    assert "chapter" in data


def test_curriculum_response_uses_chapters_field():
    response = get_curriculum_response()
    assert response.chapters[0].name == "Ułamki Zwykłe"
    assert response.chapters[0].topics[0].name == "Zapisywanie"


def test_function_registry_contains_only_generators():
    for name, func in FUNCTION_REGISTRY.items():
        assert not name.startswith("_")
        assert getattr(func, "__module__", "").startswith("backend.chapters")


def test_rejects_missing_topics_key(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "Bad_Topic.yaml"
    bad_yaml.write_text(
        """
chapter: "Bad Topic"
id: 1
keyboard_type: "default"
skills:
  - id: 10
    name: "No topics key"
    levels:
      - level: 1
        name: "Lvl 1"
        function: "frac_write_1"
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    loader._load_curriculum_store.cache_clear()

    with pytest.raises(loader.CurriculumLoadError, match="topics"):
        loader.get_curriculum()


def test_rejects_unknown_generator_function(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "Bad_Topic.yaml"
    bad_yaml.write_text(
        """
chapter: "Bad Topic"
id: 1
keyboard_type: "default"
topics:
  - id: 10
    name: "Broken"
    levels:
      - level: 1
        name: "Lvl 1"
        function: "nonexistent_generator"
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    loader._load_curriculum_store.cache_clear()

    with pytest.raises(loader.CurriculumLoadError, match="nonexistent_generator"):
        loader.get_curriculum()


def test_rejects_duplicate_chapter_name(tmp_path, monkeypatch):
    path1 = tmp_path / "a.yaml"
    path2 = tmp_path / "b.yaml"
    path1.write_text("placeholder", encoding="utf-8")
    path2.write_text("placeholder", encoding="utf-8")

    skill: loader.TopicDict = {
        "topic_id": 10,
        "name": "Skill",
        "max_level": 1,
        "radio_only": False,
    }
    topics_meta = (skill,)
    bundle = loader.ChapterBundle(
        chapter_id=1,
        chapter_name="Dup Chapter",
        keyboard_type="default",
        raw={},
        topics_meta=topics_meta,
        topics_by_id=loader._derive_topics_by_id(list(topics_meta)),
        level_configs={},
        topic_name_by_id=loader._derive_topic_name_by_id(list(topics_meta)),
    )

    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    monkeypatch.setattr(loader, "_validate_file", lambda _fp, _data: bundle)
    loader._load_curriculum_store.cache_clear()

    with pytest.raises(loader.CurriculumLoadError, match="Duplicate chapter id"):
        loader.get_curriculum()


def test_rejects_filename_chapter_mismatch(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "Wrong_Name.yaml"
    bad_yaml.write_text(
        """
chapter: "Correct Name"
id: 1
keyboard_type: "default"
topics:
  - id: 10
    name: "Skill"
    levels:
      - level: 1
        name: "Lvl 1"
        function: "frac_write_1"
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    loader._load_curriculum_store.cache_clear()

    with pytest.raises(loader.CurriculumLoadError, match="filename must be"):
        loader.get_curriculum()
