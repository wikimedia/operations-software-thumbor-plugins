import pytest

from wikimedia_thumbor.denylist import deny_reason, load_denylist

RULES = """
rules:
  - {glob: "*.stl", reason: STL is off}
  - {glob: "*.png", min_bytes: 1000}
"""


def load(tmp_path, content):
    path = tmp_path / "deny-rules.yaml"
    path.write_text(content)
    return load_denylist(str(path))


def test_missing_file(tmp_path):
    assert load_denylist(str(tmp_path / "nope.yaml")) == []


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("rules: [unclosed\n", id="invalid-yaml"),
        pytest.param("rules:\n  - {glob: '*.png', min_size: 1000}\n", id="unknown-key"),
        pytest.param("rules:\n  - {glob: '*.png', min_bytes: big}\n", id="bad-min-bytes"),
    ],
)
def test_invalid_file_denies_nothing(tmp_path, content):
    assert load(tmp_path, content) == []


@pytest.mark.parametrize(
    "path, size, expected",
    [
        pytest.param("a/ab/Book.djvu", None, None, id="unmatched"),
        pytest.param("a/ab/Triceratops.STL", None, "STL is off", id="case-insensitive"),
        pytest.param("archive/a/ab/20200101000000!Triceratops.stl", None, "STL is off", id="archived"),
        pytest.param("a/ab/Bayeux.png", None, None, id="size-unknown"),
        pytest.param("a/ab/Bayeux.png", 999, None, id="below-min-bytes"),
        pytest.param("a/ab/Bayeux.png", 1000, "Thumbnailing a/ab/Bayeux.png is disabled", id="at-min-bytes"),
    ],
)
def test_deny_reason(tmp_path, path, size, expected):
    assert deny_reason(load(tmp_path, RULES), path, size) == expected
