# QML Notes

This contains a collection of good to know things when working with QML and Python.

## Property Binding

One of the nice properties of QML is that it has property binding, i.e. it can be directly fed with values from any `QtObject` based instance if it exposes its values properly. This can be achieved through the following:

```{python}
from Pyside2 import QtCore, QtQML

class DemoModel(QtCore.QObject):
    
    variableChanged = QtCore.Signal()
    
    def __init__(self, parent=None)
    	super().__init__(parent)
        
        self._variable = "Test"

    def _get_variable(self) -> str:
        return self._variable
    
    def _set_variable(self, value: str) -> None:
        if value == self._variable:
            return
        
        self._variable = value
        self.variableChanged.emit()
    
    variable = QtCore.Property(
    	str,
        fget=_get_variable,
        fset=_set_variable,
        notify=variableChanged
    )
```

The above skeleton exposes the `variable` member to QML and will notify the QML side when the value of `variable` is changed. However, if the QML content representing the value of `variable` changes this is not sent back to the Python side. Apparently this two way communication is not support by QML and given this was the case back in 2010 it does not seem likely to ever be added. In order to support such a two way synchronization the QML side needs to actively updated the Python side.

```{qml}
Item {
	property DemoModel model

	TextField {
		text: model.variable
		
		onTextChanged: {
			model.variable = text
		}
	}
}
```

The above QML snippet populates the textfield with the value of the `variable` from the above model class. Any changes to the value of `variable` via Python code will notify the QML side and update the visual representation accordingly. To send changes back to the Python model instance the `onTextChanged` signal needs to added. To prevent a binding loop the `_set_variable` method needs to ensure the provided value is different from the currently stored one, as otherwise a event loop would be possible.

## Python Function Return Values for QML

It is possible to call Python functions which return a value from QML as long as these are defined as `Slot` in a `QtCore` derived class. The `gremlin.ui.backend` class is a good example of a class making use of this.

```{python}
import random

from Pyside2 import QtCore

class Backend(QtCore):
    
    def __init__(self, parent=None):
        super().__init__(parent)
   	
    @QtCore.Slot(int, int, result=int)
    def randomInt(self, min_val: int, max_val: int) -> int:
		return random.randint(min_val, max_val)
```

This allows the method to be called from within any QML file which has access to the an instance of the `Backend` class.

## Model Classes with Custom Attribute Names

Accessing data from a Python model via custom names is the more convenient then having to deal with possibly changing indices. This is readily supported by QML by specifying additional model roles in the Python model being visualized via QML.

```{python}
from typing import Any, Dict
from PySide2 import QtCore, QtQML

class ColorModel(QtCore.QAbstractListModel):
    
    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("rgb".encode()),
    }
    
    def __init__(self, parent: None):
        super().__init__(parent)
        
        self._colors = []
    
    def rowCount(self, parent: QtCore.QModelIndex=...) -> int:
        return len(self._colors)
    
    def data(self, index: QtCore.QModelIndex, role: int=...) -> Any:
		if role not in ColorModel.roles:
			raise("Invalid role specified")
        
        role_name = SimpleModel.roles[role].data().decode()
        if role_name == "name":
            return self._colors[index.row].name
       	elif role_name == "rgb":
            return self._colors[index.row].rgb

	def roleNames(self) -> Dict:
        return ColorModel.roles
```

The above example specifies a simple class which holds colors. To permit QML to access the properties, i.e. name and rgb code, of each color via name the `roles` dictionary is defined and exposed. Without this there is no way to access these properties via name.

## ListView

Frequently models will contain a list of identical items that need to be visualized. As these items might be taking up more space then the ListView component has in the UI it is capable of scrolling. To turn the ListView into a container that has a scroll bar and behaves properly, i.e. like a desktop application and not a phone app the following setup is recommended.

```{qml}
ListView {
    id: idListView
    anchors.fill: parent

    // Make it behave like a sensible scrolling container
    ScrollBar.vertical: ScrollBar {}
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds

    // Content to visualize
    model: model
    delegate: idDelegate
}

Component {
	id: idDelegate
	
	...
}
```

## Simple List Models

At times it is useful to return a simple list of strings to be displayed by a QML view or repeater. Providing the model via property causes some issues as QML is not happy with the actual data types exposed by PySide2. As such to specify the correct type of `QVariantList` the type information has to be provided as a string.

```{python}
from PySide2 import QtCore

@QtCore.Property(type="QVariantList")
def listData():
    return ["List", "of", "Strings"]
```

This model can now be used by any QML element that can handle a list model.

## Drag & Drop

To implement drag & drop with QML three components are needed.

- The item to be dragged has to specify the correct `Drag.*` properties
- An area which acts as the drag handle has to be specified using, for example, a `MouseArea`
- An area onto which the dragged object can be dropped has to be specified using the `DropArea`

The behavior of the drag & drop system changes drastically based on the `Drag.dragType` value. Using the default value the `Drag.onDragStarted` event is not available (likely others not either). The setup that worked out for the desired behavior in Gremlin is the following:

**Item Drag values**

```
Drag.dragType: Drag.automatic
Drag.active: idDragArea.drag.active
Drag.supportedActions: Qt.MoveAction
Drag.proposedAction: Qt.MoveAction
Drag.mimeData: {
	"text/plain": model.id
}

Drag.onDragFinished: {
	idBaseItem.dragSuccess = dropAction == Qt.MoveAction;
}
Drag.onDragStarted: {
	idBaseItem.sourceY = idBaseItem.y
}
```

**Drag handle**

```
MouseArea {
	id: idDragArea

    drag.target: idBaseItem
    drag.axis: Drag.YAxis

    onReleased: {
        if(!idBaseItem.dragSuccess)
        {
	        // Reset item position
        }
    }

    // Create an image of the object to visualize the dragging
    onPressed: idBaseItem.grabToImage(function(result) {
    	idBaseItem.Drag.imageSource = result.url
    })
}
```

**Drop Area**

```
DropArea {
    id: idDropArea

    height: idBaseItem.height
    anchors.left: idBaseItem.left
    anchors.right: idBaseItem.right
    anchors.top: idBaseItem.verticalCenter

    // Visualization of the drop indicator
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.verticalCenter

	    height: 5

        opacity: idDropArea.containsDrag ? 1.0 : 0.0
        color: "red"
    }

    onDropped: {
    	// Signal that the drop was successful
        drop.accept();
    
    	// Handle model change
    	if(drop.text != model.id)
        {
	        idListView.model.moveAfter(drop.text, model.id);
        }
    }
}
```

The above is not a generic setup that can be directly used as it relies on and makes assumptions about the model and intended behavior. However, the general flow should be applicable to other UI elements. The base item's `Drag.onDragFinished` sets a flag which is used by the `MouseArea.onReleased` event to reset the position of the item if needed. The `DropArea.onDropped` event handler ensures the `Drag.onDragFinished` is notified of success and then goes on to handle model changes that are in line with the intended drag & drop behavior.

## Icon Colors

Icons on buttons and the like by default will be rendered black and white. This is caused by the tinting ability associated with colors. To display the icon's actual colors the `color` property of the `icon` has to be set to `transparent`.

```qml
// This results in the icon being shown using the colors defined in the image file
Button {
	icon.source: "path/to/icon.png"
	icon.color: "transparent"
}

// This results in the icon being shown in red
Button {
	icon.source: "path/to/icon.png"
	icon.color: "red"
}
```

## Python Object to QML Life Time

Returning a QML object instance from Python to QML code will in most cases fail to work as the Python object will be cleaned up, resulting in QML seeing a `null` object. The correct way to work around this is to use the `parent` parameter available to every `QtObject` based class. As such when creating an object in Python which is intended as a return type to QML UI code the `parent` parameter of the object should never be `None` but rather an instance of another QML object which will persist longer than the new object being created.

