// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

.pragma library
.import QtQml as QQ

function createComponent(componentSpec, parent)
{
    let component = Qt.createComponent(componentSpec);
    if(component.status == QQ.Component.Error) {
        console.log(component.errorString())
    }
    else if((component.status == QQ.Component.Ready))
    {
        let window = component.createObject(parent, {"x": 100, "y": 300});
        window.show();
    }
}

function capitalize(value)
{
    return value.replace(/\b\w/g, l => l.toUpperCase())
}

function selectText(value, text1, text2)
{
    return value ? text1 : text2
}

// Maps a UserFeedback.FeedbackType severity (Info=1, Warning=2, Error=3) to
// an AppIcon name.
function hintIcon(type) {
    switch(type) {
        case 2:
            return "warning"
        case 3:
            return "error"
        default:
            return "help"
    }
}

// Maps a UserFeedback.FeedbackType severity to an AppIcon role.
function hintRole(type) {
    switch(type) {
        case 2:
            return "warning"
        case 3:
            return "error"
        default:
            return "fg"
    }
}

function determineHintIcon(userFeedback) {
    // Extract the highest severity feedback type from the list of user
    // feedback entries.
    let highestSeverity = 0;
    for (let i = 0; i < userFeedback.length; i++) {
        if (userFeedback[i]["type"] > highestSeverity) {
            highestSeverity = userFeedback[i]["type"];
        }
    }
    return hintIcon(highestSeverity)
}

function determineHintRole(userFeedback) {
    // Extract the highest severity feedback type from the list of user
    // feedback entries.
    let highestSeverity = 0;
    for (let i = 0; i < userFeedback.length; i++) {
        if (userFeedback[i]["type"] > highestSeverity) {
            highestSeverity = userFeedback[i]["type"];
        }
    }
    return hintRole(highestSeverity)
}
