# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from gremlin.ui import log_viewer


@pytest.fixture
def logger(request: pytest.FixtureRequest) -> Iterator[logging.Logger]:
    logger = logging.getLogger(f"test-log-viewer-{request.node.name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    yield logger
    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_evicted_chars_match_evicted_record(logger: logging.Logger) -> None:
    handler = log_viewer.LogViewerHandler(max_records=2)
    logger.addHandler(handler)
    emitted: list[tuple[int, str, int]] = []
    handler.notifier.recordAdded.connect(
        lambda sequence, text, evicted: emitted.append((sequence, text, evicted))
    )

    logger.info("first\nsecond line")
    logger.info("abc")
    logger.info("xy")
    logger.info("z")

    assert [evicted for _, _, evicted in emitted] == [
        0,
        0,
        len("first\nsecond line") + 1,
        4,
    ]
    assert handler.snapshot() == ("xy\nz", 4)


def test_source_skips_records_contained_in_snapshot(logger: logging.Logger) -> None:
    handler = log_viewer.LogViewerHandler()
    logger.addHandler(handler)
    logger.info("a")
    logger.info("b")

    source = log_viewer.LogSource()
    source.loggerName = logger.name
    appended: list[tuple[str, int]] = []
    source.recordAppended.connect(
        lambda text, evicted: appended.append((text, evicted))
    )

    assert source.snapshot() == "a\nb"
    # Late delivery of a queued signal for a record already in the snapshot.
    handler.notifier.recordAdded.emit(2, "b", 0)
    logger.info("c")

    assert appended == [("c", 0)]
