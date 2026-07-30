// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick

// Specialization of RowDropBand accepting only action drags (SPEC §8), for plugins with their
// own action-container slots (Chain, Condition, Tempo, ...) that need a drop target for the
// empty/first-item case. RowDropBand is a sibling primitive in this same module.
RowDropBand {
    validationCallback: function(drop) {
        return drop.getDataAsString("type") === "action"
    }
}
