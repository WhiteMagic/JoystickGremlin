# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Reads hints from a CSV file and makes them available to Gremlin for use."""

from __future__ import annotations

import csv

from gremlin.util import resource_path

# Stores the hints and allows Gremlin to grab the ones it needs for display
hint = {}


try:
    with open(resource_path("doc/hints.csv")) as csv_stream:
        reader = csv.reader(csv_stream, delimiter=",", quotechar='"')
        for row in reader:
            hint[row[0]] = row[1]
except FileNotFoundError:
    pass
