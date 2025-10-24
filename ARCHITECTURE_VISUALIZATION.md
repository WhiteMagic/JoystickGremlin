# Joystick Gremlin - Abhängigkeitsvisualisierung

## Hauptmodule und ihre Abhängigkeiten

### 1. Core Architecture

```mermaid
graph TB
    subgraph "UI Layer"
        UI[gremlin/ui/*]
        QML[QML Views]
    end
    
    subgraph "Application Layer"
        MAIN[joystick_gremlin.py]
        EH[event_handler]
        MM[mode_manager]
        PM[plugin_manager]
    end
    
    subgraph "Domain Layer"
        PROFILE[profile]
        BASE[base_classes]
        ACTIONS[action_plugins/*]
    end
    
    subgraph "Infrastructure Layer"
        LINPUT[linput/*]
        DM[device_manager]
        KM[keyboard_mouse]
        VO[virtual_output]
    end
    
    subgraph "External Dependencies - Linux"
        EVDEV[evdev]
        PYUDEV[pyudev]
        PYNPUT[pynput]
        UINPUT[python-uinput]
        QT[PySide6]
    end
    
    subgraph "Legacy Windows - ENTFERNEN"
        DILL[dill]
        VJOY[vjoy]
        WIN32[win32*]
    end
    
    UI --> MAIN
    UI --> QT
    QML --> QT
    
    MAIN --> EH
    MAIN --> MM
    MAIN --> PM
    MAIN --> LINPUT
    
    EH --> BASE
    EH --> PROFILE
    MM --> BASE
    
    PROFILE --> BASE
    ACTIONS --> BASE
    
    LINPUT --> EVDEV
    LINPUT --> PYUDEV
    LINPUT --> PYNPUT
    LINPUT --> UINPUT
    
    DM --> LINPUT
    KM --> LINPUT
    VO --> LINPUT
    
    classDef uiClass fill:#FFE5B4,stroke:#333,stroke-width:2px
    classDef appClass fill:#90EE90,stroke:#333,stroke-width:2px
    classDef domainClass fill:#87CEEB,stroke:#333,stroke-width:2px
    classDef infraClass fill:#DDA0DD,stroke:#333,stroke-width:2px
    classDef linuxClass fill:#98FB98,stroke:#333,stroke-width:3px
    classDef windowsClass fill:#FF6B6B,stroke:#333,stroke-width:3px,stroke-dasharray: 5 5
    
    class UI,QML uiClass
    class MAIN,EH,MM,PM appClass
    class PROFILE,BASE,ACTIONS domainClass
    class LINPUT,DM,KM,VO infraClass
    class EVDEV,PYUDEV,PYNPUT,UINPUT,QT linuxClass
    class DILL,VJOY,WIN32 windowsClass
```

### 2. Zyklische Abhängigkeiten (KRITISCH!)

```mermaid
graph LR
    BC[base_classes]
    PROF[profile]
    EH[event_handler]
    CR[code_runner]
    UIP[ui.profile]
    UAM[ui.action_model]
    ROOT[action_plugins.root]
    
    BC -->|imports| PROF
    PROF -->|imports| BC
    
    BC -->|imports| EH
    EH -->|imports| CR
    CR -->|imports| BC
    
    UIP -->|imports| UAM
    UAM -->|imports| UIP
    
    UIP -->|imports| ROOT
    ROOT -->|imports| UIP
    
    classDef cycleClass fill:#FF6B6B,stroke:#333,stroke-width:3px
    class BC,PROF,EH,CR,UIP,UAM,ROOT cycleClass
```

### 3. Module-Größe Übersicht

```mermaid
graph TD
    subgraph "SEHR GROSS > 1000 Zeilen"
        RES[resources.py<br/>20,104 Zeilen]
        UIDEV[ui.device.py<br/>1,473 Zeilen]
        PROF2[profile.py<br/>1,259 Zeilen]
        UTIL[util.py<br/>1,040 Zeilen]
    end
    
    subgraph "GROSS 500-1000 Zeilen"
        VJOY2[vjoy.py<br/>984 Zeilen]
        MACRO[macro.py<br/>920 Zeilen]
        UIPROF[ui.profile.py<br/>906 Zeilen]
        APMACRO[action_plugins.macro<br/>781 Zeilen]
        TYPES[types.py<br/>729 Zeilen]
        DILL2[dill.py<br/>681 Zeilen]
    end
    
    subgraph "MITTEL 200-500 Zeilen"
        REST[...weitere 90 Module...]
    end
    
    classDef veryLarge fill:#8B0000,color:#fff,stroke:#333,stroke-width:3px
    classDef large fill:#DC143C,color:#fff,stroke:#333,stroke-width:2px
    classDef medium fill:#FFA500,stroke:#333,stroke-width:1px
    
    class RES,UIDEV,PROF2,UTIL veryLarge
    class VJOY2,MACRO,UIPROF,APMACRO,TYPES,DILL2 large
    class REST medium
```

### 4. Lange Funktionen (Clean Code Verstöße)

```mermaid
graph LR
    subgraph "Top 5 Längste Funktionen"
        F1[make_gremlin_app<br/>179 Zeilen]
        F2[generate_report<br/>149 Zeilen]
        F3[create_shortcuts<br/>131 Zeilen]
        F4[table_data<br/>92 Zeilen]
        F5[code_runner.start<br/>88 Zeilen]
    end
    
    F1 -.->|AUFTEILEN| F1A[_parse_arguments<br/>20 Zeilen]
    F1 -.->|AUFTEILEN| F1B[_configure_logging<br/>15 Zeilen]
    F1 -.->|AUFTEILEN| F1C[_create_qt_app<br/>25 Zeilen]
    F1 -.->|AUFTEILEN| F1D[_setup_plugins<br/>20 Zeilen]
    
    classDef longFunc fill:#FF6B6B,color:#fff,stroke:#333,stroke-width:2px
    classDef shortFunc fill:#90EE90,stroke:#333,stroke-width:1px
    
    class F1,F2,F3,F4,F5 longFunc
    class F1A,F1B,F1C,F1D shortFunc
```

### 5. Windows-Abhängigkeiten Übersicht

```mermaid
graph TB
    subgraph "Zu Entfernende Windows-Abhängigkeiten"
        W1[dill<br/>Device ID Generation]
        W2[vjoy<br/>Virtual Joystick]
        W3[win32gui<br/>Process Monitor]
        W4[win32process<br/>Process Monitor]
        W5[win32com.client<br/>TTS]
        W6[ctypes.wintypes<br/>Windows Types]
    end
    
    subgraph "Linux Ersatz"
        L1[uuid<br/>Standard Library]
        L2[linput.VirtualJoystick<br/>uinput-basiert]
        L3[psutil<br/>Cross-platform]
        L4[psutil<br/>Cross-platform]
        L5[espeak/festival<br/>Linux TTS]
        L6[Nicht benötigt]
    end
    
    W1 -.->|ERSETZEN| L1
    W2 -.->|ERSETZEN| L2
    W3 -.->|ERSETZEN| L3
    W4 -.->|ERSETZEN| L4
    W5 -.->|ERSETZEN| L5
    W6 -.->|ENTFERNEN| L6
    
    classDef winClass fill:#FF6B6B,color:#fff,stroke:#333,stroke-width:2px
    classDef linuxClass fill:#90EE90,stroke:#333,stroke-width:2px
    
    class W1,W2,W3,W4,W5,W6 winClass
    class L1,L2,L3,L4,L5,L6 linuxClass
```

### 6. Neue Architektur (Clean Code Refactoring)

```mermaid
graph TD
    subgraph "Presentation Layer"
        V[Views<br/>QML]
        VM[ViewModels<br/>Python]
    end
    
    subgraph "Application Layer"
        APP[Application Services<br/>event_handler, mode_manager]
        BUS[Event Bus<br/>Lose Kopplung]
    end
    
    subgraph "Domain Layer"
        DOM[Domain Models<br/>Profile, Actions, Events]
        INT[Interfaces<br/>IDeviceManager, IVirtualDevice]
    end
    
    subgraph "Infrastructure Layer"
        IMPL[Implementations<br/>LinuxDeviceManager, LinuxVirtualDevice]
    end
    
    V --> VM
    VM --> BUS
    BUS --> APP
    APP --> DOM
    DOM --> INT
    INT <-.implementiert von.-| IMPL
    
    classDef presClass fill:#FFE5B4,stroke:#333,stroke-width:2px
    classDef appClass fill:#90EE90,stroke:#333,stroke-width:2px
    classDef domClass fill:#87CEEB,stroke:#333,stroke-width:2px
    classDef infraClass fill:#DDA0DD,stroke:#333,stroke-width:2px
    
    class V,VM presClass
    class APP,BUS appClass
    class DOM,INT domClass
    class IMPL infraClass
```

### 7. Refactoring Phasen

```mermaid
gantt
    title Refactoring Roadmap
    dateFormat  YYYY-MM-DD
    
    section Phase 1
    Windows-Abhängigkeiten entfernen    :p1, 2025-10-24, 14d
    
    section Phase 2
    Zyklische Abhängigkeiten auflösen   :p2, after p1, 7d
    
    section Phase 3
    Lange Funktionen aufteilen          :p3, after p2, 7d
    
    section Phase 4
    Große Module aufteilen              :p4, after p3, 14d
    
    section Phase 5
    Architektur-Verbesserungen          :p5, after p4, 21d
```

## Metriken Vorher/Nachher

| Metrik | Vorher | Ziel (Nachher) |
|--------|--------|----------------|
| **Zyklische Abhängigkeiten** | 5 | 0 ✅ |
| **Windows-Abhängigkeiten** | 10+ | 0 ✅ |
| **Funktionen > 50 Zeilen** | 20 | 0 ✅ |
| **Module > 500 Zeilen** | 16 | < 5 ✅ |
| **Durchschn. Kopplung** | 8.5 | < 5 ✅ |
| **Test Coverage** | ~30% | > 70% ✅ |
| **Pylint Score** | 6.8 | > 8.0 ✅ |

## Clean Code Prinzipien

### SOLID
- ✅ **S**ingle Responsibility - Eine Funktion, eine Verantwortlichkeit
- ✅ **O**pen/Closed - Offen für Erweiterung, geschlossen für Modifikation
- ✅ **L**iskov Substitution - Interfaces verwenden
- ✅ **I**nterface Segregation - Kleine, fokussierte Interfaces
- ✅ **D**ependency Inversion - Von Abstraktionen abhängen, nicht Implementierungen

### Weitere Prinzipien
- 📏 **Funktionslänge** < 50 Zeilen
- 📦 **Modulgröße** < 500 Zeilen
- 🔗 **Kopplung** < 8 Abhängigkeiten
- 🎯 **Kohäsion** Hoch (verwandte Funktionen zusammen)
- 🔄 **DRY** Don't Repeat Yourself
- 💡 **KISS** Keep It Simple, Stupid
- 🧪 **Testbarkeit** Dependency Injection, Interfaces

## Zusammenfassung

Die Analyse hat **kritische Probleme** identifiziert:

⚠️ **5 zyklische Abhängigkeiten** die die Wartbarkeit stark beeinträchtigen
⚠️ **10+ Windows-Abhängigkeiten** die noch entfernt werden müssen
⚠️ **20 lange Funktionen** die gegen Single Responsibility verstoßen
⚠️ **16 große Module** die aufgeteilt werden sollten

Der **Refactoring-Plan** adressiert alle Probleme systematisch in 5 Phasen über ca. 2-3 Monate.

Nach Abschluss wird der Code:
✅ Vollständig Linux-nativ ohne Windows-Abhängigkeiten
✅ Keine zyklischen Abhängigkeiten
✅ Alle Funktionen und Module in angemessener Größe
✅ Höhere Testabdeckung und Wartbarkeit
✅ Bessere Architektur mit klaren Schichten
