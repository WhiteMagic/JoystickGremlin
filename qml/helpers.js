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