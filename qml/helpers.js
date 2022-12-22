function createComponent(componentSpec)
{
    var component = Qt.createComponent(componentSpec);
    var window = component.createObject(_root, {"x": 100, "y": 300});
    window.show();
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