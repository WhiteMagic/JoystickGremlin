# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import scripts.lint_style as lint_style

_STYLE_QML_DIR = pathlib.Path(__file__).parents[2] / "style" / "qml"


def test_shipped_kobold_style_is_clean() -> None:
    assert lint_style.scan_tree(_STYLE_QML_DIR) == []


def test_raw_hex_color_detected(tmp_path: pathlib.Path) -> None:
    (tmp_path / "Bad.qml").write_text("Rectangle { color: '#ff0000' }")

    violations = lint_style.scan_tree(tmp_path)

    assert [v.rule for v in violations] == ["raw-hex-color"]


def test_raw_px_detected(tmp_path: pathlib.Path) -> None:
    (tmp_path / "Bad.qml").write_text("Rectangle { width: 13 }")

    violations = lint_style.scan_tree(tmp_path)

    assert [v.rule for v in violations] == ["raw-px"]


def test_forbidden_effect_detected(tmp_path: pathlib.Path) -> None:
    (tmp_path / "Bad.qml").write_text("Rectangle { color: Qt.rgba(1, 0, 0, 0.5) }")

    violations = lint_style.scan_tree(tmp_path)

    assert [v.rule for v in violations] == ["forbidden-effect"]


def test_point_size_detected(tmp_path: pathlib.Path) -> None:
    (tmp_path / "Bad.qml").write_text("Text { font.pointSize: 12 }")

    violations = lint_style.scan_tree(tmp_path)

    assert [v.rule for v in violations] == ["point-size"]


def test_metrics_and_theme_references_pass_clean(tmp_path: pathlib.Path) -> None:
    (tmp_path / "Good.qml").write_text(
        "Rectangle {\n"
        "    width: Metrics.ctrlH * 2\n"
        "    color: Theme.bg\n"
        "    border.width: Metrics.hairline\n"
        "    anchors.margins: -2\n"
        "}\n"
    )

    assert lint_style.scan_tree(tmp_path) == []


def test_violation_inside_comment_ignored(tmp_path: pathlib.Path) -> None:
    (tmp_path / "Commented.qml").write_text(
        "// width: 13 -- this used to be a bug, fixed below\n"
        "Rectangle { width: Metrics.ctrlH }\n"
    )

    assert lint_style.scan_tree(tmp_path) == []
