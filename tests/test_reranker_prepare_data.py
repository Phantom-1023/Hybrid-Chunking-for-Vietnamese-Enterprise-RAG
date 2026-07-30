import pytest

from training.reranker.prepare_data import prepare_groups


def _manifest():
    return {
        "label_contract": "context-zero-verified",
        "source_sha256": "snapshot",
        "splits": {
            "train": [{"row_index": 0}],
            "dev": [{"row_index": 1}],
            "test": [{"row_index": 2}],
        },
    }


def _rows():
    return [
        {
            "question": f"question {index}",
            "answer": f"answer {index}",
            "context": [
                f"positive answer {index}",
                f"negative one {index}",
                f"negative two {index}",
            ],
        }
        for index in range(3)
    ]


def test_prepare_groups_inherits_split_and_has_no_pair_conflicts():
    groups, manifest = prepare_groups(_rows(), _manifest())

    assert len(groups["train"]) == 1
    assert groups["train"][0]["positive"] == "positive answer 0"
    assert len(groups["train"][0]["negatives"]) == 2
    assert all(value == 0 for value in manifest["cross_split_pair_conflicts"].values())


def test_multiple_positive_candidate_is_not_used_as_negative():
    rows = _rows()
    rows[0]["answer"] = "shared answer"
    rows[0]["context"] = [
        "primary evidence for shared answer",
        "another passage containing shared answer",
        "real negative",
    ]

    groups, manifest = prepare_groups(rows, _manifest())

    assert groups["train"][0]["negatives"] == ["real negative"]
    assert manifest["splits"]["train"]["multiple_positive_exclusions"] == 1


def test_prepare_groups_fails_without_verified_contract():
    manifest = _manifest()
    manifest["label_contract"] = "context-zero-assumed"

    with pytest.raises(ValueError, match="not verified"):
        prepare_groups(_rows(), manifest)
