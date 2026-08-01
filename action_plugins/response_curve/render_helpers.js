// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

function draw_curve(ctx, points, width, height) {
    width /= 2
    height /= 2

    ctx.moveTo((points[0].x + 1) * width, (height * 2) - (points[0].y + 1) * height);
    for (let i = 1; i < points.length; i++) {
        let x = (points[i].x + 1) * width
        let y = (height * 2) - (points[i].y + 1) * height
        ctx.lineTo(x, y);
    }
    ctx.stroke();
}

function draw_background(ctx, width, height)
{
    ctx.drawImage("grid.png", 0, 0, width, height);
}

function clamp(val, min, max) {
    return Math.min(Math.max(val, min), max)
}

function x2u(x, parent_x, size, offset) {
    return parent_x + ((x + 1) / 2 * size) - offset
}

function y2v(y, parent_y, size, offset) {
    return parent_y + (size - ((y + 1) / 2 * size)) - offset
}

// The -2 is required for the x and y coordinate provided
// by QML to actually be correct and result in no change
// without mouse motion
function u2x(u, offset, size) {
    return (2 * ((u + offset - 2) / size)) - 1
}

function v2y(v, offset, size) {
    return (-2 * ((v + offset - 2) / size)) + 1
}

// The curve is always stored on a [-1, 1] range in both axes, which the
// numerical displays can present as a 0 to 100 range instead. Since both axes
// are scaled by the same factor, slopes are identical in either presentation
// and only positions and lengths need converting.
//
// The offset is applied after the scaling in one direction and before it in
// the other so that converting a value and converting it back returns the
// exact same number, leaving values untouched when the scale is switched.
function to_percent(value) {
    return value * 50 + 50
}

function from_percent(value) {
    return (value - 50) / 50
}

function length_to_percent(value) {
    return value * 50
}

function length_from_percent(value) {
    return value / 50
}