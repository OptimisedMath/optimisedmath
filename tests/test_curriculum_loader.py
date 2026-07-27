"""Tests for curriculum YAML loading and validation."""

from pathlib import Path

import pytest

import backend.curriculum_loader as loader
import backend.engine as engine


@pytest.fixture(autouse=True)
def reset_curriculum_cache():
    loader._load_curriculum_store.cache_clear()
    loader.set_function_registry(engine.FUNCTION_REGISTRY)
    yield
    loader._load_curriculum_store.cache_clear()
    loader.set_function_registry(engine.FUNCTION_REGISTRY)


def test_loads_real_curriculum_with_micro_topics():
    curriculum = loader.get_curriculum()
    assert "Ułamki Zwykłe" in curriculum
    assert "Ułamki Dziesiętne" in curriculum
    assert curriculum["Ułamki Zwykłe"][0]["name"] == "Zapisywanie"


def test_macro_topics_ordered_by_yaml_order():
    ordered = loader.get_macro_topics_ordered()
    assert ordered.index("Ułamki Zwykłe") < ordered.index("Ułamki Dziesiętne")


def test_get_macro_yaml_uses_micro_topics_key():
    data = loader.get_macro_yaml("Ułamki Zwykłe")
    assert "micro_topics" in data
    assert "topics" not in data


def test_curriculum_response_uses_micro_topics_field():
    response = engine.get_curriculum_response()
    assert response.macro_topics[0] == "Ułamki Zwykłe"
    assert "Ułamki Zwykłe" in response.micro_topics
    assert response.micro_topics["Ułamki Zwykłe"][0].name == "Zapisywanie"


def test_function_registry_contains_only_generators():
    for name, func in engine.FUNCTION_REGISTRY.items():
        assert not name.startswith("_")
        assert getattr(func, "__module__", "").startswith("backend.macro_topics")


def test_rejects_missing_micro_topics_key(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "Bad_Topic.yaml"
    bad_yaml.write_text(
        """
macro_topic: "Bad Topic"
order: 1
keyboard_type: "default"
topics:
  - order: 10
    name: "Legacy key"
    levels:
      - level: 1
        name: "Lvl 1"
        function: "frac_write_1"
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    loader._load_curriculum_store.cache_clear()

    with pytest.raises(loader.CurriculumLoadError, match="micro_topics"):
        loader.get_curriculum()


def test_rejects_unknown_generator_function(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "Bad_Topic.yaml"
    bad_yaml.write_text(
        """
macro_topic: "Bad Topic"
order: 1
keyboard_type: "default"
micro_topics:
  - order: 10
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


def test_rejects_duplicate_macro_topic(tmp_path, monkeypatch):
    path1 = tmp_path / "a.yaml"
    path2 = tmp_path / "b.yaml"
    path1.write_text("placeholder", encoding="utf-8")
    path2.write_text("placeholder", encoding="utf-8")

    micro_topics_meta = (
        {
            "micro_topic_order": 10,
            "name": "Skill",
            "max_level": 1,
            "text_mode_disabled": False,
        },
    )
    bundle = loader.MacroTopicBundle(
        macro_topic="Dup Macro",
        order=1,
        keyboard_type="default",
        raw={},
        micro_topics_meta=micro_topics_meta,
        topic_map=loader._derive_topic_map(list(micro_topics_meta)),
        level_configs={},
        micro_topic_name_by_order=loader._derive_micro_topic_name_by_order(
            list(micro_topics_meta)
        ),
    )

    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    monkeypatch.setattr(loader, "_validate_file", lambda _fp, _data: bundle)
    loader._load_curriculum_store.cache_clear()

    with pytest.raises(loader.CurriculumLoadError, match="Duplicate macro_topic"):
        loader.get_curriculum()


def test_rejects_filename_macro_mismatch(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "Wrong_Name.yaml"
    bad_yaml.write_text(
        """
macro_topic: "Correct Name"
order: 1
keyboard_type: "default"
micro_topics:
  - order: 10
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
