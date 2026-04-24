"""生成本地确定性主题报告的 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_agent.pipeline.report import generate_topic_report


def build_parser() -> argparse.ArgumentParser:
    """Build the topic report CLI parser."""
    parser = argparse.ArgumentParser(description="Generate a local topic analysis report.")
    parser.add_argument("--index", default="data/index/tfidf_index.pkl", help="Path to the TF-IDF index file.")
    parser.add_argument("--topic", required=True, help="Topic to analyze.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of search results to include.")
    parser.add_argument("--language", choices=("auto", "ja", "zh", "en"), default="ja", help="Output language.")
    parser.add_argument("--output", default="outputs/reports/topic_report.md", help="Output Markdown path.")
    return parser


def main() -> None:
    """Generate a local topic report and print a short preview."""
    parser = build_parser()
    args = parser.parse_args()

    result = generate_topic_report(
        index_path=Path(args.index),
        topic=args.topic,
        top_k=args.top_k,
        language=args.language,
        output_path=Path(args.output) if args.output else None,
    )

    print(f"topic={result['topic']}")
    print(f"risk_level={result['risk_level']}")
    print(f"risk_score={result['risk_score']:.4f}")
    print(f"result_count={result['result_count']}")
    print(f"output_path={result['output_path']}")
    print("preview=" + result["report"][:240].replace("\n", " "))


if __name__ == "__main__":
    main()
