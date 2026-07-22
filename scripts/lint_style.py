# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Static lint for the Kobold style tree.

Scans style/qml/**/*.qml for the mechanically-checkable rules from
doc/design/kobold_style/jg_style_architecture_design.md §2: colours only
from Theme, dimensions only from Metrics, no shadow/gradient/tint effects,
font sizes only via Metrics.

Run with `poetry run python scripts/lint_style.py`.
"""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import sys

# Properties where a bare numeric literal is a styling-position violation.
_DIMENSION_PROPERTIES = (
    "width",
    "height",
    "implicitWidth",
    "implicitHeight",
    "spacing",
    "margins",
    "margin",
    "radius",
    "border.width",
    "font.pixelSize",
    "padding",
    "leftPadding",
    "rightPadding",
    "topPadding",
    "bottomPadding",
    "x",
    "y",
)

# Bare literals sanctioned by the architecture guide.
_ALLOWED_LITERALS = {
    "0",  # zero is dimensionless: disables/collapses a size, not a size itself
    "-2",  # focus-ring outset (anchors.margins: -2), guide §4.5 / Phase 2 DoD
    "2",  # focus-ring stroke width (border.width: 2), same fixed constant
}

_HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_FORBIDDEN_EFFECT_RE = re.compile(
    r"box-shadow|gradient|Qt\.rgba\(|color-mix|layer\.effect"
    r"|Qt\.lighter\(|Qt\.darker\(|Qt\.tint\("
)
_POINT_SIZE_RE = re.compile(r"\bpointSize\b")
_DIMENSION_ASSIGNMENT_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in _DIMENSION_PROPERTIES) + r")"
    r"\s*:\s*(-?\d+(?:\.\d+)?)\b"
)


@dataclasses.dataclass(frozen=True)
class Violation:
    """A single lint finding, tied to its source location."""

    path: pathlib.Path
    line: int
    rule: str
    text: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.text.strip()}"


def _strip_comments(source: str) -> str:
    """Blanks out // and /* */ comments while preserving line numbers.

    Args:
        source: Raw QML source text.

    Returns:
        The source with comment bodies removed but line breaks intact.
    """
    source = re.sub(r"//[^\n]*", "", source)
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


def scan_file(path: pathlib.Path) -> list[Violation]:
    """Scans a single .qml file for lint violations.

    Args:
        path: Path of the .qml file to scan.

    Returns:
        Violations found, in source order.
    """
    violations: list[Violation] = []
    code = _strip_comments(path.read_text(encoding="utf-8"))
    for lineno, line in enumerate(code.splitlines(), start=1):
        if _HEX_COLOR_RE.search(line):
            violations.append(Violation(path, lineno, "raw-hex-color", line))
        if _FORBIDDEN_EFFECT_RE.search(line):
            violations.append(Violation(path, lineno, "forbidden-effect", line))
        if _POINT_SIZE_RE.search(line):
            violations.append(Violation(path, lineno, "point-size", line))
        for match in _DIMENSION_ASSIGNMENT_RE.finditer(line):
            if match.group(2) not in _ALLOWED_LITERALS:
                violations.append(Violation(path, lineno, "raw-px", line))
    return violations


def scan_tree(root: pathlib.Path) -> list[Violation]:
    """Scans every .qml file under root for lint violations.

    Args:
        root: Directory to scan recursively.

    Returns:
        Violations found, sorted by file then line.
    """
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.qml")):
        violations.extend(scan_file(path))
    return violations


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: scans a directory and prints any violations.

    Args:
        argv: Command-line arguments, defaulting to sys.argv.

    Returns:
        Process exit code: 0 if clean, 1 if violations were found.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "style" / "qml",
        help="Directory to scan (default: style/qml).",
    )
    args = parser.parse_args(argv)

    violations = scan_tree(args.root)
    for violation in violations:
        print(violation)
    if violations:
        print(f"\n{len(violations)} style lint violation(s).", file=sys.stderr)
        return 1
    print("Style lint clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
