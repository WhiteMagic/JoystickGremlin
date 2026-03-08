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

function formatUserFeedback(userFeedback)
{
    if (!userFeedback || userFeedback.length === 0) {
        return "";
    }

    // Replicate Python backend type codes.
    const FeedbackType = {
        Info: 1,
        Warning: 2,
        Error: 3
    };

    let html = "<ul style='list-style-type: none; margin: 0; padding-left: 0;'>";
    for (let i = 0; i < userFeedback.length; i++) {
        let color = "";
        let icon = "";
        switch(userFeedback[i][0]) {
            case FeedbackType.Info:
                color = "#4A9EFF";
                icon = "ℹ";
                break;
            case FeedbackType.Warning:
                color = "#FFA500";
                icon = "⚠";
                break;
            case FeedbackType.Error:
                color = "#FF4444";
                icon = "✖";
                break;
            default:
                color = "#FFFFFF";
                icon = "•";
        }

        // Use padding-left and text-indent to create hanging indent for wrapped text.
        html += `<li style='padding-left: 1.5em; text-indent: -1.5em;'>`;
        html += `<font color='${color}'>${icon}</font> ${userFeedback[i][1]}`;
        html += `</li>`;
    }
    html += "</ul>";

    return html;
}
