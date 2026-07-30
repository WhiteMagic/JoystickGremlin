// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import Kobold.Foundation

// Plain 1px rule for separating rows within an action's config body.
// Fixed to Theme.line -- no color property, no checked/selected state -- so
// there is nothing here that could grow into an R4 (accent-as-fill) violation.
Rectangle {
    implicitHeight: Metrics.hairline
    color: Theme.line
}
