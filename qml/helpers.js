function createComponent(componentSpec)
{
    var component = Qt.createComponent(componentSpec);
    var window = component.createObject(root, {"x": 100, "y": 300});
    window.show();
}

function pythonizePath(path)
{
    var tmp_path = path.toString()
    return tmp_path.replace(/^(file:\/{3})/, "");
}