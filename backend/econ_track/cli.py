from __future__ import annotations

import argparse
import logging

from econ_track.build import write_dataset


def main() -> None:
    """Parse CLI arguments and run the requested data-generation command."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    parser = argparse.ArgumentParser(description="Generate static Econ Track data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate static dashboard JSON")
    generate.add_argument("--config", default="config/funds.json")
    generate.add_argument("--output", default="frontend/public/data/latest.json")
    generate.add_argument("--no-keep-last-good", action="store_true")

    args = parser.parse_args()
    if args.command == "generate":
        dataset = write_dataset(args.config, args.output, keep_last_good=not args.no_keep_last_good)
        status = "ok" if dataset.get("status", {}).get("ok") else "warning"
        print(f"wrote {args.output} ({status})")


if __name__ == "__main__":
    main()
