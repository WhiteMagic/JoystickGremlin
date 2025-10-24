# CLEAN CODE REFACTORING-PLAN für Joystick Gremlin

## Executive Summary

Die Analyse hat **kritische Probleme** identifiziert, die gegen Clean Code Prinzipien verstoßen:

- ⚠️ **5 zyklische Abhängigkeiten** (Verletzung von SOLID-Prinzipien)
- ⚠️ **20 lange Funktionen** (> 50 Zeilen - Verletzung Single Responsibility)
- ⚠️ **10+ Windows-Abhängigkeiten** die noch nicht entfernt wurden
- ⚠️ **16 große Module** (> 500 Zeilen - niedrige Kohäsion)
- ⚠️ **Hohe Kopplung** in mehreren Modulen

## Priorität 1: Windows-Abhängigkeiten vollständig entfernen

### 1.1 gremlin/util.py - DILL entfernen

**Problem:**
```python
import dill
from dill import GUID
```

**Refactoring:**
```python
# Ersetze DILL GUID mit UUID (bereits in linput verwendet)
import uuid

def generate_device_id() -> uuid.UUID:
    """Generiert eine plattformunabhängige Device-ID."""
    return uuid.uuid4()
```

**Dateien betroffen:**
- `gremlin/util.py`
- `gremlin/profile.py` (nutzt GUID)
- `gremlin/device_helpers.py`

---

### 1.2 gremlin/user_script.py - DILL und vJoy entfernen

**Problem:**
```python
import dill
from vjoy.vjoy import VJoyProxy
```

**Refactoring:**
```python
# Ersetze vJoy mit linput.VirtualJoystick
import linput

# Verwende abstraktes Interface
from abc import ABC, abstractmethod

class IVirtualDevice(ABC):
    @abstractmethod
    def set_axis(self, axis: int, value: float): ...
    
    @abstractmethod
    def set_button(self, button: int, pressed: bool): ...

class LinuxVirtualDevice(IVirtualDevice):
    def __init__(self, device_id: int):
        self._vjoy = linput.VirtualJoystick.get(device_id)
    
    def set_axis(self, axis: int, value: float):
        self._vjoy.set_axis(axis, value)
    
    def set_button(self, button: int, pressed: bool):
        self._vjoy.set_button(button, pressed)
```

**Dateien betroffen:**
- `gremlin/user_script.py` (1192 Zeilen!)
- `gremlin/device_helpers.py`
- `action_plugins/map_to_vjoy/*`

---

### 1.3 gremlin/process_monitor.py - Windows-spezifisch

**Problem:** Gesamte Datei ist Windows-only:
```python
import ctypes.wintypes
import win32gui
import win32process
```

**Refactoring:**
```python
# Neu: gremlin/linux_process_monitor.py
import psutil  # Bereits in requirements.txt!
import re
from typing import Optional

class LinuxProcessMonitor:
    """Linux-native Prozessüberwachung mit psutil."""
    
    def __init__(self):
        self._monitored_processes: Dict[str, int] = {}
    
    def is_process_running(self, process_name: str) -> bool:
        """Prüft ob ein Prozess läuft."""
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if re.match(process_name, proc.info['name'], re.I):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def get_active_window_process(self) -> Optional[str]:
        """Ermittelt den Prozess des aktiven Fensters (X11/Wayland)."""
        # Implementierung mit Xlib oder python-xlib
        # Für Wayland: ggf. gdbus/dbus
        pass
```

**Dateien betroffen:**
- `gremlin/process_monitor.py` → ENTFERNEN
- Neu: `gremlin/linux_process_monitor.py`

---

### 1.4 gremlin/tts.py - Windows TTS ersetzen

**Problem:**
```python
import win32com.client
```

**Refactoring:**
```python
# Neu: gremlin/linux_tts.py
import subprocess
from typing import Optional

class LinuxTTS:
    """Linux Text-to-Speech mit espeak oder festival."""
    
    def __init__(self, backend: str = 'espeak'):
        self.backend = backend
        self._check_availability()
    
    def _check_availability(self):
        """Prüft ob TTS verfügbar ist."""
        try:
            subprocess.run([self.backend, '--version'], 
                         capture_output=True, check=True)
        except FileNotFoundError:
            raise RuntimeError(f"TTS backend '{self.backend}' nicht installiert")
    
    def speak(self, text: str, rate: int = 150):
        """Gibt Text als Sprache aus."""
        if self.backend == 'espeak':
            subprocess.Popen(['espeak', f'-s{rate}', text])
        elif self.backend == 'festival':
            subprocess.Popen(['echo', text, '|', 'festival', '--tts'])
```

**Dateien betroffen:**
- `gremlin/tts.py` → Komplett ersetzen

---

### 1.5 vjoy/vjoy.py - VJoy Modul entfernen

**Status:** Komplett Windows-spezifisch, bereits durch `linput/virtual_output.py` ersetzt

**Action:** 
```bash
# Markiere als deprecated
mv vjoy vjoy_deprecated_windows_only
# Update alle Imports zu linput.VirtualJoystick
```

---

## Priorität 2: Zyklische Abhängigkeiten auflösen

### 2.1 Zyklus: base_classes ↔ profile

**Problem:**
```
gremlin.base_classes → gremlin.profile → gremlin.base_classes
```

**Ursache:** Beide Module importieren sich gegenseitig

**Refactoring:**
```python
# Lösung: Gemeinsame Abstraktion extrahieren
# Neu: gremlin/domain/abstractions.py

from abc import ABC, abstractmethod
from typing import Protocol

class IProfileElement(Protocol):
    """Basis-Interface für Profilelemente."""
    def to_xml(self) -> str: ...
    def from_xml(self, node) -> None: ...

class IAction(Protocol):
    """Basis-Interface für Actions."""
    def execute(self, event): ...
```

**Anwenden:**
```python
# gremlin/base_classes.py
from gremlin.domain.abstractions import IProfileElement

# gremlin/profile.py  
from gremlin.domain.abstractions import IProfileElement
# KEIN Import von base_classes mehr!
```

---

### 2.2 Zyklus: base_classes → event_handler → code_runner → base_classes

**Problem:** Drei-Wege Zyklus

**Refactoring:**
```python
# Dependency Inversion Principle anwenden
# Neu: gremlin/domain/events.py

class EventBus:
    """Zentraler Event-Bus (Mediator Pattern)."""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
    
    def subscribe(self, event_type: str, callback):
        self._subscribers[event_type].append(callback)
    
    def publish(self, event_type: str, data):
        for callback in self._subscribers[event_type]:
            callback(data)

# Verwendung:
# base_classes.py publiziert Events
# event_handler.py subscribed Events
# code_runner.py subscribed Events
# KEINE direkten Imports mehr!
```

---

### 2.3 Zyklus: ui.profile ↔ ui.action_model

**Problem:**
```
gremlin.ui.profile → gremlin.ui.action_model → gremlin.ui.profile
```

**Refactoring:**
```python
# Model-View-ViewModel Pattern anwenden
# Neu: gremlin/ui/viewmodels/action_viewmodel.py

class ActionViewModel:
    """ViewModel für Actions - entkoppelt UI von Domain."""
    
    def __init__(self, action):
        self._action = action
        self.property_changed = Signal()
    
    @property
    def name(self) -> str:
        return self._action.name
    
    @name.setter
    def name(self, value: str):
        self._action.name = value
        self.property_changed.emit('name', value)
```

---

## Priorität 3: Lange Funktionen aufteilen (Single Responsibility)

### 3.1 joystick_gremlin.make_gremlin_app (179 Zeilen!)

**Refactoring:**
```python
# Aufteilen in logische Komponenten:

def make_gremlin_app(argv):
    args = _parse_arguments(argv)
    _configure_logging()
    _setup_configuration()
    
    app = _create_qt_application(argv)
    engine = _create_qml_engine(app)
    backend = _register_backend(engine)
    
    _load_plugins(backend)
    _initialize_ui(engine)
    _load_initial_profile(backend, args)
    
    app.aboutToQuit.connect(shutdown_cleanup)
    return app

def _parse_arguments(argv) -> argparse.Namespace:
    """Parst Kommandozeilenargumente."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Path to profile")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--start-minimized", action="store_true")
    return parser.parse_known_args(argv)[0]

def _configure_logging() -> None:
    """Konfiguriert System- und User-Logging."""
    for logger_config in [_system_logger_config(), _user_logger_config()]:
        configure_logger(logger_config)

def _create_qt_application(argv) -> QtWidgets.QApplication:
    """Erstellt und konfiguriert Qt-Applikation."""
    _setup_qt_environment()
    app = QtWidgets.QApplication(argv)
    app.setWindowIcon(QtGui.QIcon("gfx/icon.png"))
    app.setApplicationDisplayName("Joystick Gremlin")
    return app

# usw...
```

---

### 3.2 linput/device_manager._convert_evdev_event (79 Zeilen)

**Refactoring:**
```python
# Strategy Pattern für Event-Konvertierung

class EventConverter(ABC):
    @abstractmethod
    def can_convert(self, evdev_event) -> bool: ...
    
    @abstractmethod
    def convert(self, evdev_event) -> Optional[Event]: ...

class ButtonEventConverter(EventConverter):
    def can_convert(self, ev) -> bool:
        return ev.type == evdev.ecodes.EV_KEY
    
    def convert(self, ev) -> Optional[Event]:
        return Event(
            event_type=EventType.JoystickButton,
            identifier=ev.code,
            is_pressed=(ev.value == 1),
            # ...
        )

class AxisEventConverter(EventConverter):
    # ...

class HatEventConverter(EventConverter):
    # ...

class EventConverterChain:
    def __init__(self):
        self._converters = [
            ButtonEventConverter(),
            AxisEventConverter(),
            HatEventConverter()
        ]
    
    def convert(self, evdev_event) -> Optional[Event]:
        for converter in self._converters:
            if converter.can_convert(evdev_event):
                return converter.convert(evdev_event)
        return None
```

---

## Priorität 4: Große Module aufteilen

### 4.1 gremlin/util.py (1,040 Zeilen)

**Refactoring:**
```
gremlin/util/
├── __init__.py
├── file_operations.py     # FileWatcher, read_bool, read_int, etc.
├── xml_helpers.py         # XML parsing utilities
├── path_utils.py          # resource_path, userprofile_path, etc.
├── ui_helpers.py          # display_error, QtWidgets helpers
├── decorators.py          # @throttle, timing decorators
└── validators.py          # Validation functions
```

---

### 4.2 gremlin/profile.py (1,259 Zeilen)

**Refactoring:**
```
gremlin/profile/
├── __init__.py
├── profile.py             # Haupt-Profile Klasse
├── device_profile.py      # DeviceProfile
├── mode.py                # Mode Klasse
├── input_item.py          # InputItem Hierarchie
├── serialization.py       # XML Serialization
└── migration.py           # Profile Migration/Upgrade
```

---

### 4.3 gremlin/ui/device.py (1,473 Zeilen)

**Refactoring:**
```
gremlin/ui/device/
├── __init__.py
├── device_widget.py       # Haupt-Device Widget
├── input_identifier.py    # InputIdentifier Widgets
├── calibration.py         # Calibration UI
├── device_models.py       # QML Models
└── device_tabs.py         # Tab-Widgets
```

---

## Priorität 5: Architektur-Verbesserungen

### 5.1 Schichtenarchitektur (Layered Architecture)

```
┌─────────────────────────────────────────┐
│  Presentation Layer (gremlin/ui/)       │
│  - QML Views                            │
│  - ViewModels                           │
│  - UI Backend                           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Application Layer (gremlin/)           │
│  - event_handler.py                     │
│  - mode_manager.py                      │
│  - plugin_manager.py                    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Domain Layer (gremlin/domain/)         │
│  - profile.py                           │
│  - actions.py                           │
│  - events.py (Event Bus)                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Infrastructure Layer (linput/)         │
│  - device_manager.py                    │
│  - keyboard_mouse.py                    │
│  - virtual_output.py                    │
└─────────────────────────────────────────┘
```

**Regeln:**
- Obere Schichten dürfen nur untere Schichten importieren
- Dependency Inversion für Plattform-spezifischen Code
- Keine Zyklus zwischen Schichten

---

### 5.2 Dependency Injection Container

```python
# Neu: gremlin/di_container.py

class DIContainer:
    """Dependency Injection Container für bessere Testbarkeit."""
    
    def __init__(self):
        self._singletons = {}
        self._factories = {}
    
    def register_singleton(self, interface, implementation):
        """Registriert einen Singleton."""
        self._singletons[interface] = implementation()
    
    def register_factory(self, interface, factory):
        """Registriert eine Factory."""
        self._factories[interface] = factory
    
    def resolve(self, interface):
        """Löst eine Abhängigkeit auf."""
        if interface in self._singletons:
            return self._singletons[interface]
        if interface in self._factories:
            return self._factories[interface]()
        raise ValueError(f"No registration for {interface}")

# Verwendung:
container = DIContainer()
container.register_singleton(IDeviceManager, linput.DeviceManager)
container.register_singleton(IVirtualOutput, linput.VirtualJoystick)

# In Code:
device_manager = container.resolve(IDeviceManager)
```

---

### 5.3 Event-Driven Architecture

```python
# Neu: gremlin/domain/event_bus.py

from typing import Callable, Dict, List
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    DEVICE_ADDED = "device_added"
    DEVICE_REMOVED = "device_removed"
    MODE_CHANGED = "mode_changed"
    PROFILE_LOADED = "profile_loaded"
    INPUT_EVENT = "input_event"

@dataclass
class DomainEvent:
    event_type: EventType
    data: any

class EventBus:
    """Zentraler Event-Bus für lose Kopplung."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = defaultdict(list)
        return cls._instance
    
    def subscribe(self, event_type: EventType, handler: Callable):
        self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        for handler in self._handlers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                logging.error(f"Event handler error: {e}")
```

---

## Implementierungs-Roadmap

### Phase 1: Windows-Abhängigkeiten (1-2 Wochen)
- [ ] 1.1 DILL aus util.py entfernen
- [ ] 1.2 vJoy aus user_script.py entfernen
- [ ] 1.3 process_monitor.py durch linux_process_monitor.py ersetzen
- [ ] 1.4 tts.py durch linux_tts.py ersetzen
- [ ] 1.5 vjoy/ Verzeichnis entfernen

### Phase 2: Zyklische Abhängigkeiten (1 Woche)
- [ ] 2.1 base_classes ↔ profile auflösen
- [ ] 2.2 base_classes → event_handler → code_runner auflösen
- [ ] 2.3 ui.profile ↔ ui.action_model auflösen

### Phase 3: Funktionen refactoren (1 Woche)
- [ ] 3.1 make_gremlin_app aufteilen
- [ ] 3.2 _convert_evdev_event aufteilen
- [ ] 3.3 Weitere lange Funktionen

### Phase 4: Module aufteilen (2 Wochen)
- [ ] 4.1 util.py → util/ Package
- [ ] 4.2 profile.py → profile/ Package
- [ ] 4.3 ui/device.py → ui/device/ Package

### Phase 5: Architektur (2-3 Wochen)
- [ ] 5.1 Schichtenarchitektur einführen
- [ ] 5.2 DI Container implementieren
- [ ] 5.3 Event Bus implementieren

---

## Testing-Strategie

Für jedes Refactoring:

1. **Vor dem Refactoring:** Unit Tests schreiben
2. **Während des Refactorings:** Tests grün halten
3. **Nach dem Refactoring:** Integration Tests

```python
# Beispiel: Test für Event Converter Refactoring

def test_button_event_converter():
    converter = ButtonEventConverter()
    evdev_event = MockEvdevEvent(
        type=evdev.ecodes.EV_KEY,
        code=304,  # BTN_SOUTH
        value=1
    )
    
    result = converter.convert(evdev_event)
    
    assert result.event_type == EventType.JoystickButton
    assert result.identifier == 304
    assert result.is_pressed == True

def test_event_converter_chain():
    chain = EventConverterChain()
    
    # Test Button
    button_event = MockEvdevEvent(type=evdev.ecodes.EV_KEY)
    assert chain.convert(button_event) is not None
    
    # Test Axis
    axis_event = MockEvdevEvent(type=evdev.ecodes.EV_ABS)
    assert chain.convert(axis_event) is not None
```

---

## Erfolgsmetriken

Nach Abschluss des Refactorings:

- ✅ **0 zyklische Abhängigkeiten**
- ✅ **0 Windows-Abhängigkeiten** (außer in deprecated/)
- ✅ **Alle Funktionen < 50 Zeilen**
- ✅ **Alle Module < 500 Zeilen** (außer auto-generierte wie resources.py)
- ✅ **Kopplung < 8 Abhängigkeiten** pro Modul
- ✅ **Test Coverage > 70%**
- ✅ **Pylint Score > 8.0**

---

## Nächste Schritte

1. Review dieses Refactoring-Plans
2. Priorisierung mit Team abstimmen
3. Branch erstellen: `refactoring/clean-code-phase-1`
4. Phase 1 starten: Windows-Abhängigkeiten
5. Pull Requests für jedes abgeschlossene Item

---

*Erstellt mit der Abhängigkeitsanalyse vom Oktober 2025*
