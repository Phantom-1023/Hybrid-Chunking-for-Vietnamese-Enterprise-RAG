from pathlib import Path

from training.reranker.train import (
    checkpoint_tree_sha256,
    flatten_examples,
    mrr_at_k_from_group_scores,
)


def test_flatten_examples_creates_positive_and_negative_pairs():
    examples = flatten_examples(
        [
            {
                "question": "q",
                "positive": "p",
                "negatives": ["n1", "n2"],
            }
        ]
    )

    assert examples == [
        ("q", "p", 1.0),
        ("q", "n1", 0.0),
        ("q", "n2", 0.0),
    ]


def test_mrr_uses_positive_rank_within_cutoff():
    assert mrr_at_k_from_group_scores([(0.5, [0.8, 0.1])], k=5) == 0.5
    assert mrr_at_k_from_group_scores([(0.1, [0.9] * 5)], k=5) == 0.0


def test_checkpoint_tree_hash_is_stable(tmp_path: Path):
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "weights.bin").write_bytes(b"weights")

    first = checkpoint_tree_sha256(tmp_path)
    second = checkpoint_tree_sha256(tmp_path)

    assert first == second
