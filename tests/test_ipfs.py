import pytest
from app.utils.ipfs import sanitize_metadata, validate_cid


def test_sanitize_removes_script_tags():
    data = {
        "name": "My NFT",
        "description": "<script>alert(1)</script>Nice",
        "nested": {"info": "<script>bad</script>good"},
    }
    clean = sanitize_metadata(data)
    assert "<script" not in clean.get("description", "")
    assert clean["description"] == "Nice"
    assert clean["nested"]["info"] == "good"


def test_sanitize_truncates_long_fields():
    long_str = "a" * 2000
    data = {"note": long_str}
    clean = sanitize_metadata(data)
    assert len(clean["note"]) <= 1000


def test_validate_cid_accepts_common_formats():
    assert validate_cid("QmYwAPJzv5CZsnAzt8auVTLW3s2jS") is True or validate_cid("Qm123")


def test_validate_cid_rejects_invalid():
    assert not validate_cid("")
    assert not validate_cid("not a cid!!")
