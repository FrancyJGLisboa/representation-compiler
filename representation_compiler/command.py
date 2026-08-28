"""Portable user-facing entry point: ``repr learn``."""
from __future__ import annotations

import argparse

from .protocol import learning_invocation, material_reference


def main() -> None:
    parser = argparse.ArgumentParser(prog="repr", description="Representation Compiler commands")
    commands = parser.add_subparsers(dest="command", required=True)
    learn = commands.add_parser("learn", help="Create a representation-discovery task packet for any agent")
    learn.add_argument("material", help="A local transcript/file path, URL, or pasted material")
    learn.add_argument("--goal", required=True, help="What the learner needs to understand")
    args = parser.parse_args()
    if args.command == "learn":
        print(learning_invocation(args.goal, material_reference(args.material)))


if __name__ == "__main__":
    main()
