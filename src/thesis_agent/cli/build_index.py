"""构建本地 TF-IDF 检索索引的 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_agent.pipeline.retrieval import build_tfidf_index


def build_parser() -> argparse.ArgumentParser:
    """Build the index CLI argument parser."""
    parser = argparse.ArgumentParser(description="Build a local TF-IDF index from chunk JSONL.")
    parser.add_argument("--chunks", default="data/processed/chunks.jsonl", help="Input chunks JSONL path.")
    parser.add_argument("--output", default="data/index/tfidf_index.pkl", help="Output TF-IDF index path.")
    parser.add_argument("--language", choices=("auto", "ja", "zh", "en"), default="ja", help="Document language.")
    parser.add_argument("--analyzer", default="char", help="TF-IDF analyzer type.")
    parser.add_argument("--ngram-min", type=int, default=2, help="Minimum character n-gram size.")
    parser.add_argument("--ngram-max", type=int, default=5, help="Maximum character n-gram size.")
    return parser


def main() -> None:
    """Run the local TF-IDF index build."""
    parser = build_parser()
    args = parser.parse_args()

    stats = build_tfidf_index(
        chunks_path=Path(args.chunks),
        index_output=Path(args.output),
        language=args.language,
        analyzer=args.analyzer,
        ngram_min=args.ngram_min,
        ngram_max=args.ngram_max,
    )

    print(f"chunk_count={stats['chunk_count']}")
    print(f"index_output={stats['index_output']}")
    print(f"analyzer={stats['analyzer']}")
    print(f"ngram_range={stats['ngram_range']}")
    print(f"language={stats['language']}")


if __name__ == "__main__":
    main()
