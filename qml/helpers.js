// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

function createComponent(componentSpec)
{
    let component = Qt.createComponent(componentSpec);
    if(component.status == Component.Error) {
        console.log(component.errorString())
    }
    else if((component.status == Component.Ready))
    {
        let window = component.createObject(_root, {"x": 100, "y": 300});
        window.show();
    }
}

function pythonizePath(path)
{
    var tmp_path = path.toString()
    return tmp_path.replace(/^(file:\/{3})/, "");
}

function capitalize(value)
{
    return value.replace(/\b\w/g, l => l.toUpperCase())
}

function selectText(value, text1, text2)
{
    return value ? text1 : text2
}

function safeText(text, backup)
{
    return !text ? backup : text
}

function hintIcon(type) {
    switch(type) {
        case 1:
            return "\uF433";
        case 2:
            return "\uF33B";
        case 3:
            return "\uF337";
        default:
            return "\uF505";
    }
}

function hintColor(type) {
    switch(type) {
        case 1:
            return "#3E65FF";
        case 2:
            return "#F0A30A";
        case 3:
            return "#A20025";
        default:
            return "#74008b";
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

function determineHintColor(userFeedback) {
    // Extract the highest severity feedback type from the list of user
    // feedback entries.
    let highestSeverity = 0;
    for (let i = 0; i < userFeedback.length; i++) {
        if (userFeedback[i]["type"] > highestSeverity) {
            highestSeverity = userFeedback[i]["type"];
        }
    }
    return hintColor(highestSeverity)
}
