================================================================================
JOYSTICK GREMLIN - ABHÄNGIGKEITSANALYSE & CLEAN CODE REFACTORING
================================================================================

## 1. PROJEKTÜBERSICHT
   Gesamtanzahl Module: 104
   Gesamtzeilen Code: 50,273
   Gesamtanzahl Funktionen: 1783
   Gesamtanzahl Klassen: 276

## 2. EXTERNE ABHÄNGIGKEITEN
   Linux-native Bibliotheken:
   - evdev
   - pynput
   - pyudev

   Qt/UI Bibliotheken:
   - PyQt5
   - PySide6
   - PySide6.QtCore
   - PySide6.QtMultimedia

   Legacy Windows-Abhängigkeiten (ENTFERNEN!):
   ⚠️  - ctypes.wintypes
   ⚠️  - dill
   ⚠️  - vjoy
   ⚠️  - vjoy.vjoy
   ⚠️  - vjoy.vjoy_interface
   ⚠️  - win32api
   ⚠️  - win32com.client
   ⚠️  - win32con
   ⚠️  - win32gui
   ⚠️  - win32process

## 3. ZYKLISCHE ABHÄNGIGKEITEN (CLEAN CODE VERSTOSSE)
   ⚠️  Gefundene zyklische Abhängigkeiten: 3
   1. gremlin.base_classes -> gremlin.profile -> gremlin.base_classes
   2. gremlin.ui.profile -> gremlin.ui.action_model -> gremlin.ui.profile
   3. gremlin.ui.profile -> action_plugins.root -> gremlin.ui.profile

## 4. LANGE FUNKTIONEN (> 50 Zeilen - Clean Code Verstoß)
   ⚠️  Gefundene lange Funktionen: 20
   - joystick_gremlin.make_gremlin_app: 179 Zeilen
   - analyze_dependencies.generate_report: 149 Zeilen
   - generate_wix.create_shortcuts: 131 Zeilen
   - gremlin.cheatsheet.table_data: 92 Zeilen
   - gremlin.code_runner.start: 88 Zeilen
   - generate_wix.create_document: 80 Zeilen
   - linput.device_manager._convert_evdev_event: 79 Zeilen
   - linput.device_manager._create_device_summary: 74 Zeilen
   - linput.virtual_output.create: 70 Zeilen
   - gremlin.code_runner._virtual_event_setup: 66 Zeilen

## 5. HOCHGEKOPPELTE MODULE (> 10 Abhängigkeiten)
   ⚠️  Module mit hoher Kopplung: 1
   - action_plugins.merge_axis: 12 Abhängigkeiten

## 6. GROSSE MODULE (> 500 Zeilen)
   ⚠️  Große Module: 16
   - resources: 20,104 Zeilen
   - gremlin.ui.device: 1,473 Zeilen
   - gremlin.profile: 1,269 Zeilen
   - gremlin.util: 1,041 Zeilen
   - deprecated_windows_only.vjoy.vjoy: 984 Zeilen
   - gremlin.macro: 920 Zeilen
   - gremlin.ui.profile: 906 Zeilen
   - action_plugins.macro: 781 Zeilen
   - gremlin.types: 729 Zeilen
   - deprecated_windows_only.dill: 681 Zeilen

## 7. CLEAN CODE REFACTORING-EMPFEHLUNGEN

### 7.1 Kritische Windows-Abhängigkeiten entfernen:
   - gremlin.util: Entfernt dill, GUID Imports
   - gremlin.user_script: Entfernt dill, vjoy Imports
   - gremlin.device_helpers: Entfernt vjoy.VJoyProxy
   - gremlin.process_monitor: Komplett Windows-spezifisch (win32gui, ctypes.wintypes)
   - gremlin.tts: win32com.client ersetzen mit Linux TTS
   - gremlin.windows_event_hook: Komplett entfernen

### 7.2 Funktionen aufteilen (Single Responsibility):
   - joystick_gremlin.make_gremlin_app (179 Zeilen) → In kleinere Funktionen aufteilen
   - analyze_dependencies.generate_report (149 Zeilen) → In kleinere Funktionen aufteilen
   - generate_wix.create_shortcuts (131 Zeilen) → In kleinere Funktionen aufteilen
   - gremlin.cheatsheet.table_data (92 Zeilen) → In kleinere Funktionen aufteilen
   - gremlin.code_runner.start (88 Zeilen) → In kleinere Funktionen aufteilen

### 7.3 Abhängigkeiten reduzieren:
   - action_plugins.merge_axis (12 Deps) → Dependency Injection nutzen

### 7.4 Große Module aufteilen:
   - resources (20,104 Zeilen) → In mehrere Module aufteilen
   - gremlin.ui.device (1,473 Zeilen) → In mehrere Module aufteilen
   - gremlin.profile (1,269 Zeilen) → In mehrere Module aufteilen

## 8. ARCHITEKTUR-VERBESSERUNGEN

### 8.1 Schichtenarchitektur einführen:
   ```
   [UI Layer - PySide6]
        ↓
   [Application Layer - gremlin.*]
        ↓
   [Domain Layer - event_handler, profile, etc.]
        ↓
   [Infrastructure Layer - linput.*]
   ```

### 8.2 Dependency Inversion Principle:
   - Interfaces/Abstrakte Klassen für Plattform-Abhängigkeiten
   - LinuxInputProvider implementiert IInputProvider
   - VirtualOutputProvider implementiert IVirtualDevice

### 8.3 Single Responsibility:
   - event_handler.py: Nur Event-Routing, keine Business Logic
   - sendinput.py: Nur Input-Sending, keine Event-Verarbeitung
   - device_manager.py: Nur Device-Enumeration

================================================================================

## 9. ABHÄNGIGKEITSDIAGRAMM (Mermaid)

```mermaid
graph TD
    chain[chain] --> gremlin[gremlin]
    chain[chain] --> base_classes[base_classes]
    chain[chain] --> error[error]
    chain[chain] --> profile[profile]
    chain[chain] --> types[types]
    chain[chain] --> action_model[action_model]
    chain[chain] --> profile[profile]
    change_mode[change_mode] --> gremlin[gremlin]
    change_mode[change_mode] --> base_classes[base_classes]
    change_mode[change_mode] --> profile[profile]
    change_mode[change_mode] --> types[types]
    change_mode[change_mode] --> action_model[action_model]
    change_mode[change_mode] --> profile[profile]
    common[common] --> event_handler[event_handler]
    common[common] --> types[types]
    condition[condition] --> gremlin[gremlin]
    condition[condition] --> base_classes[base_classes]
    condition[condition] --> keyboard[keyboard]
    condition[condition] --> profile[profile]
    condition[condition] --> tree[tree]
    condition[condition] --> types[types]
    condition[condition] --> action_model[action_model]
    condition[condition] --> profile[profile]
    condition[condition] --> util[util]
    comparator[comparator] --> gremlin[gremlin]
    comparator[comparator] --> base_classes[base_classes]
    comparator[comparator] --> input_cache[input_cache]
    comparator[comparator] --> types[types]
    comparator[comparator] --> profile[profile]
    description[description] --> gremlin[gremlin]
    description[description] --> base_classes[base_classes]
    description[description] --> error[error]
    description[description] --> profile[profile]
    description[description] --> types[types]
    description[description] --> action_model[action_model]
    description[description] --> profile[profile]
    double_tap[double_tap] --> gremlin[gremlin]
    double_tap[double_tap] --> base_classes[base_classes]
    double_tap[double_tap] --> config[config]
    double_tap[double_tap] --> error[error]
    double_tap[double_tap] --> profile[profile]
    double_tap[double_tap] --> tree[tree]
    double_tap[double_tap] --> types[types]
    double_tap[double_tap] --> action_model[action_model]
    double_tap[double_tap] --> profile[profile]
    dual_axis_deadzone[dual_axis_deadzone] --> gremlin[gremlin]
    dual_axis_deadzone[dual_axis_deadzone] --> base_classes[base_classes]
    dual_axis_deadzone[dual_axis_deadzone] --> error[error]
    dual_axis_deadzone[dual_axis_deadzone] --> input_cache[input_cache]
    dual_axis_deadzone[dual_axis_deadzone] --> profile[profile]
    dual_axis_deadzone[dual_axis_deadzone] --> types[types]
    dual_axis_deadzone[dual_axis_deadzone] --> action_model[action_model]
    dual_axis_deadzone[dual_axis_deadzone] --> device[device]
    dual_axis_deadzone[dual_axis_deadzone] --> profile[profile]
    dual_axis_deadzone[dual_axis_deadzone] --> util[util]
    hat_buttons[hat_buttons] --> gremlin[gremlin]
    hat_buttons[hat_buttons] --> base_classes[base_classes]
    hat_buttons[hat_buttons] --> error[error]
    hat_buttons[hat_buttons] --> plugin_manager[plugin_manager]
    hat_buttons[hat_buttons] --> profile[profile]
    hat_buttons[hat_buttons] --> types[types]
    hat_buttons[hat_buttons] --> action_model[action_model]
    hat_buttons[hat_buttons] --> profile[profile]
    load_profile[load_profile] --> gremlin[gremlin]
    load_profile[load_profile] --> base_classes[base_classes]
    load_profile[load_profile] --> error[error]
    load_profile[load_profile] --> profile[profile]
    load_profile[load_profile] --> types[types]
    load_profile[load_profile] --> ui[ui]
    load_profile[load_profile] --> action_model[action_model]
    load_profile[load_profile] --> profile[profile]
    load_profile[load_profile] --> util[util]
    macro[macro] --> gremlin[gremlin]
    macro[macro] --> base_classes[base_classes]
    macro[macro] --> error[error]
    macro[macro] --> macro[macro]
    macro[macro] --> profile[profile]
    macro[macro] --> types[types]
    macro[macro] --> action_model[action_model]
    macro[macro] --> profile[profile]
    map_to_io[map_to_io] --> gremlin[gremlin]
    map_to_io[map_to_io] --> base_classes[base_classes]
    map_to_io[map_to_io] --> error[error]
    map_to_io[map_to_io] --> event_handler[event_handler]
    map_to_io[map_to_io] --> intermediate_output[intermediate_output]
    map_to_io[map_to_io] --> profile[profile]
    map_to_io[map_to_io] --> types[types]
    map_to_io[map_to_io] --> action_model[action_model]
    map_to_io[map_to_io] --> profile[profile]
    map_to_keyboard[map_to_keyboard] --> gremlin[gremlin]
    map_to_keyboard[map_to_keyboard] --> base_classes[base_classes]
    map_to_keyboard[map_to_keyboard] --> error[error]
    map_to_keyboard[map_to_keyboard] --> profile[profile]
    map_to_keyboard[map_to_keyboard] --> types[types]
    map_to_keyboard[map_to_keyboard] --> action_model[action_model]
    map_to_keyboard[map_to_keyboard] --> profile[profile]
    map_to_mouse[map_to_mouse] --> gremlin[gremlin]
    map_to_mouse[map_to_mouse] --> base_classes[base_classes]
    map_to_mouse[map_to_mouse] --> error[error]
    map_to_mouse[map_to_mouse] --> profile[profile]
    map_to_mouse[map_to_mouse] --> types[types]
    map_to_mouse[map_to_mouse] --> action_model[action_model]
    map_to_mouse[map_to_mouse] --> profile[profile]
    map_to_vjoy[map_to_vjoy] --> gremlin[gremlin]
    map_to_vjoy[map_to_vjoy] --> base_classes[base_classes]
    map_to_vjoy[map_to_vjoy] --> profile[profile]
    map_to_vjoy[map_to_vjoy] --> types[types]
    map_to_vjoy[map_to_vjoy] --> action_model[action_model]
    map_to_vjoy[map_to_vjoy] --> profile[profile]
    merge_axis[merge_axis] --> gremlin[gremlin]
    merge_axis[merge_axis] --> base_classes[base_classes]
    merge_axis[merge_axis] --> config[config]
    merge_axis[merge_axis] --> error[error]
    merge_axis[merge_axis] --> event_handler[event_handler]
    merge_axis[merge_axis] --> input_cache[input_cache]
    merge_axis[merge_axis] --> plugin_manager[plugin_manager]
    merge_axis[merge_axis] --> profile[profile]
    merge_axis[merge_axis] --> types[types]
    merge_axis[merge_axis] --> action_model[action_model]
    merge_axis[merge_axis] --> device[device]
    merge_axis[merge_axis] --> profile[profile]
    pause_resume[pause_resume] --> gremlin[gremlin]
    pause_resume[pause_resume] --> base_classes[base_classes]
    pause_resume[pause_resume] --> error[error]
    pause_resume[pause_resume] --> profile[profile]
    pause_resume[pause_resume] --> types[types]
    pause_resume[pause_resume] --> action_model[action_model]
    pause_resume[pause_resume] --> profile[profile]
    play_sound[play_sound] --> gremlin[gremlin]
    play_sound[play_sound] --> audio_player[audio_player]
    play_sound[play_sound] --> base_classes[base_classes]
    play_sound[play_sound] --> config[config]
    play_sound[play_sound] --> error[error]
    play_sound[play_sound] --> profile[profile]
    play_sound[play_sound] --> types[types]
    play_sound[play_sound] --> action_model[action_model]
    play_sound[play_sound] --> profile[profile]
    play_sound[play_sound] --> util[util]
    reference[reference] --> gremlin[gremlin]
    reference[reference] --> base_classes[base_classes]
    reference[reference] --> error[error]
    reference[reference] --> macro[macro]
    reference[reference] --> profile[profile]
    reference[reference] --> types[types]
    reference[reference] --> action_model[action_model]
    reference[reference] --> profile[profile]
    response_curve[response_curve] --> gremlin[gremlin]
    response_curve[response_curve] --> base_classes[base_classes]
    response_curve[response_curve] --> error[error]
    response_curve[response_curve] --> profile[profile]
    response_curve[response_curve] --> types[types]
    response_curve[response_curve] --> action_model[action_model]
    response_curve[response_curve] --> profile[profile]
    response_curve[response_curve] --> util[util]
    root[root] --> gremlin[gremlin]
    root[root] --> base_classes[base_classes]
    root[root] --> config[config]
    root[root] --> error[error]
    root[root] --> profile[profile]
    root[root] --> types[types]
    root[root] --> action_model[action_model]
    root[root] --> profile[profile]
    smart_toggle[smart_toggle] --> gremlin[gremlin]
    smart_toggle[smart_toggle] --> base_classes[base_classes]
    smart_toggle[smart_toggle] --> config[config]
    smart_toggle[smart_toggle] --> error[error]
    smart_toggle[smart_toggle] --> profile[profile]
    smart_toggle[smart_toggle] --> types[types]
    smart_toggle[smart_toggle] --> action_model[action_model]
    smart_toggle[smart_toggle] --> profile[profile]
    tempo[tempo] --> gremlin[gremlin]
    tempo[tempo] --> base_classes[base_classes]
    tempo[tempo] --> config[config]
    tempo[tempo] --> error[error]
    tempo[tempo] --> profile[profile]
    tempo[tempo] --> tree[tree]
    tempo[tempo] --> types[types]
    tempo[tempo] --> action_model[action_model]
    tempo[tempo] --> profile[profile]
    vjoy[vjoy] --> error[error]
    vjoy[vjoy] --> spline[spline]
    vjoy[vjoy] --> types[types]
    vjoy_interface[vjoy_interface] --> error[error]
    dill_compat[dill_compat] -.->|Linux| linput[linput]
    dill_compat[dill_compat] -.->|Linux| types[types]
    audio_player[audio_player] --> common[common]
    audio_player[audio_player] --> config[config]
    audio_player[audio_player] --> util[util]
    base_classes[base_classes] --> gremlin[gremlin]
    base_classes[base_classes] --> domain[domain]
    base_classes[base_classes] --> error[error]
    base_classes[base_classes] --> profile[profile]
    base_classes[base_classes] --> types[types]
    cheatsheet[cheatsheet] --> gremlin[gremlin]
    cheatsheet[cheatsheet] --> keyboard[keyboard]
    code_runner[code_runner] --> gremlin[gremlin]
    code_runner[code_runner] --> base_classes[base_classes]
    code_runner[code_runner] --> types[types]
    common[common] --> gremlin[gremlin]
    common[common] --> keyboard[keyboard]
    common[common] --> types[types]
    device_helpers[device_helpers] --> gremlin[gremlin]
    device_helpers[device_helpers] --> common[common]
    device_helpers[device_helpers] --> keyboard[keyboard]
    device_helpers[device_helpers] --> types[types]
    device_initialization[device_initialization] --> gremlin[gremlin]
    device_initialization[device_initialization] -.->|Linux| linput[linput]
    domain[domain] --> types[types]
    event_handler[event_handler] --> gremlin[gremlin]
    event_handler[event_handler] --> base_classes[base_classes]
    event_handler[event_handler] --> code_runner[code_runner]
    event_handler[event_handler] --> domain[domain]
    event_handler[event_handler] --> input_cache[input_cache]
    event_handler[event_handler] --> types[types]
    event_handler[event_handler] -.->|Linux| linput[linput]
    hints[hints] --> util[util]
    input_cache[input_cache] --> gremlin[gremlin]
    input_cache[input_cache] --> common[common]
    intermediate_output[intermediate_output] --> common[common]
    intermediate_output[intermediate_output] --> error[error]
    intermediate_output[intermediate_output] --> types[types]
    keyboard[keyboard] --> gremlin[gremlin]
    linux_event_handler[linux_event_handler] --> gremlin[gremlin]
    linux_event_handler[linux_event_handler] --> base_classes[base_classes]
    linux_event_handler[linux_event_handler] --> code_runner[code_runner]
    linux_event_handler[linux_event_handler] --> input_cache[input_cache]
    linux_event_handler[linux_event_handler] --> types[types]
    linux_event_handler[linux_event_handler] -.->|Linux| linput[linput]
    linux_sendinput[linux_sendinput] --> common[common]
    linux_sendinput[linux_sendinput] --> event_handler[event_handler]
    linux_sendinput[linux_sendinput] --> types[types]
    linux_sendinput[linux_sendinput] -.->|Linux| linput[linput]
    macro[macro] --> gremlin[gremlin]
    macro[macro] --> base_classes[base_classes]
    macro[macro] --> common[common]
    macro[macro] --> config[config]
    macro[macro] --> keyboard[keyboard]
    macro[macro] --> sendinput[sendinput]
    macro[macro] --> types[types]
    mode_manager[mode_manager] --> gremlin[gremlin]
    mode_manager[mode_manager] --> common[common]
    mode_manager[mode_manager] --> config[config]
    mode_manager[mode_manager] --> error[error]
    mode_manager[mode_manager] --> types[types]
    plugin_manager[plugin_manager] --> gremlin[gremlin]
    plugin_manager[plugin_manager] --> base_classes[base_classes]
    plugin_manager[plugin_manager] --> types[types]
    profile[profile] --> gremlin[gremlin]
    profile[profile] --> base_classes[base_classes]
    profile[profile] --> domain[domain]
    profile[profile] --> intermediate_output[intermediate_output]
    profile[profile] --> tree[tree]
    profile[profile] --> types[types]
    profile[profile] --> user_script[user_script]
    profile[profile] --> util[util]
    repeater[repeater] --> gremlin[gremlin]
    repeater[repeater] --> types[types]
    sendinput[sendinput] --> common[common]
    sendinput[sendinput] --> event_handler[event_handler]
    sendinput[sendinput] --> types[types]
    sendinput[sendinput] -.->|Linux| linput[linput]
    signal[signal] --> gremlin[gremlin]
    tree[tree] --> gremlin[gremlin]
    types[types] --> error[error]
    action_model[action_model] --> gremlin[gremlin]
    action_model[action_model] --> base_classes[base_classes]
    action_model[action_model] --> domain[domain]
    action_model[action_model] --> error[error]
    action_model[action_model] --> plugin_manager[plugin_manager]
    action_model[action_model] --> profile[profile]
    action_model[action_model] --> signal[signal]
    action_model[action_model] --> types[types]
    action_model[action_model] --> profile[profile]
    backend[backend] --> gremlin[gremlin]
    backend[backend] --> audio_player[audio_player]
    backend[backend] --> intermediate_output[intermediate_output]
    backend[backend] --> signal[signal]
    backend[backend] --> device[device]
    backend[backend] --> profile[profile]
    backend[backend] --> script[script]
    backend[backend] -.->|Linux| linput[linput]
    config[config] --> config[config]
    config[config] --> types[types]
    device[device] --> gremlin[gremlin]
    device[device] --> common[common]
    device[device] --> config[config]
    device[device] --> error[error]
    device[device] --> intermediate_output[intermediate_output]
    device[device] --> signal[signal]
    device[device] --> types[types]
    profile[profile] --> base_classes[base_classes]
    profile[profile] --> error[error]
    profile[profile] --> plugin_manager[plugin_manager]
    profile[profile] --> profile[profile]
    profile[profile] --> signal[signal]
    profile[profile] --> types[types]
    profile[profile] --> action_model[action_model]
    profile[profile] --> util[util]
    script[script] --> gremlin[gremlin]
    script[script] --> error[error]
    script[script] --> profile[profile]
    script[script] --> types[types]
    script[script] --> device[device]
    util[util] --> gremlin[gremlin]
    util[util] --> types[types]
    util[util] --> gremlin[gremlin]
    util[util] --> types[types]
    windows_event_hook[windows_event_hook] --> common[common]
    windows_event_hook[windows_event_hook] --> types[types]
    joystick_gremlin[joystick_gremlin] --> config[config]
    joystick_gremlin[joystick_gremlin] --> device_initialization[device_initialization]
    joystick_gremlin[joystick_gremlin] --> error[error]
    joystick_gremlin[joystick_gremlin] --> plugin_manager[plugin_manager]
    joystick_gremlin[joystick_gremlin] --> signal[signal]
    joystick_gremlin[joystick_gremlin] --> types[types]
    joystick_gremlin[joystick_gremlin] --> backend[backend]
    joystick_gremlin[joystick_gremlin] --> config[config]
    joystick_gremlin[joystick_gremlin] --> util[util]
    joystick_gremlin[joystick_gremlin] -.->|Linux| linput[linput]
    app_tester[app_tester] --> input_cache[input_cache]
    app_tester[app_tester] --> types[types]
    conftest[conftest] --> device_initialization[device_initialization]
    conftest[conftest] --> error[error]
    conftest[conftest] --> profile[profile]
    conftest[conftest] --> backend[backend]
    test_e2e_profile_simple[test_e2e_profile_simple] --> gremlin[gremlin]
    conftest[conftest] --> device_initialization[device_initialization]
    conftest[conftest] --> event_handler[event_handler]
    test_action_condition[test_action_condition] --> gremlin[gremlin]
    test_action_condition[test_action_condition] --> error[error]
    test_action_condition[test_action_condition] --> event_handler[event_handler]
    test_action_condition[test_action_condition] --> profile[profile]
    test_action_condition[test_action_condition] --> types[types]
    test_action_description[test_action_description] --> error[error]
    test_action_description[test_action_description] --> event_handler[event_handler]
    test_action_description[test_action_description] --> profile[profile]
    test_action_description[test_action_description] --> action_model[action_model]
    test_action_description[test_action_description] --> profile[profile]
    test_action_map_to_vjoy[test_action_map_to_vjoy] --> error[error]
    test_action_map_to_vjoy[test_action_map_to_vjoy] --> profile[profile]
    test_action_map_to_vjoy[test_action_map_to_vjoy] --> types[types]
    test_action_merge[test_action_merge] --> error[error]
    test_action_merge[test_action_merge] --> profile[profile]
    test_action_merge[test_action_merge] --> types[types]
    test_action_merge[test_action_merge] --> device[device]
    test_action_root[test_action_root] --> error[error]
    test_action_root[test_action_root] --> profile[profile]
    test_action_root[test_action_root] --> types[types]
    test_action_tempo[test_action_tempo] --> config[config]
    test_action_tempo[test_action_tempo] --> error[error]
    test_action_tempo[test_action_tempo] --> profile[profile]
    test_action_tempo[test_action_tempo] --> types[types]
    test_config[test_config] --> config[config]
    test_config[test_config] --> error[error]
    test_config[test_config] --> types[types]
    test_fsm[test_fsm] --> gremlin[gremlin]
    test_intermediate_output[test_intermediate_output] --> common[common]
    test_intermediate_output[test_intermediate_output] --> error[error]
    test_intermediate_output[test_intermediate_output] --> intermediate_output[intermediate_output]
    test_modes[test_modes] --> config[config]
    test_modes[test_modes] --> error[error]
    test_modes[test_modes] --> mode_manager[mode_manager]
    test_modes[test_modes] --> plugin_manager[plugin_manager]
    test_modes[test_modes] --> profile[profile]
    test_modes[test_modes] --> shared_state[shared_state]
    test_modes[test_modes] --> types[types]
    test_profile[test_profile] --> config[config]
    test_profile[test_profile] --> error[error]
    test_profile[test_profile] --> plugin_manager[plugin_manager]
    test_profile[test_profile] --> profile[profile]
    test_profile[test_profile] --> types[types]
    test_splines[test_splines] --> spline[spline]
    test_tree[test_tree] --> error[error]
    test_tree[test_tree] --> tree[tree]
    test_util[test_util] --> error[error]
    test_util[test_util] --> types[types]
    test_util[test_util] --> util[util]
    test_linux_backend[test_linux_backend] --> device_initialization[device_initialization]
    test_linux_backend[test_linux_backend] --> event_handler[event_handler]
    test_linux_backend[test_linux_backend] --> sendinput[sendinput]
    test_linux_backend[test_linux_backend] -.->|Linux| linput[linput]
    test_linux_backend[test_linux_backend] -.->|Linux| device_manager[device_manager]
    test_linux_backend[test_linux_backend] -.->|Linux| keyboard_mouse[keyboard_mouse]
    test_linux_backend[test_linux_backend] -.->|Linux| types[types]
    test_linux_backend[test_linux_backend] -.->|Linux| virtual_output[virtual_output]

    %% Externe Abhängigkeiten
    PySide6{{"PySide6"}}
    dill{{"dill"}}
    evdev{{"evdev"}}
    pynput{{"pynput"}}
    pyudev{{"pyudev"}}
    vjoy{{"vjoy"}}

    classDef gremlinClass fill:#90EE90,stroke:#333,stroke-width:2px
    classDef linputClass fill:#87CEEB,stroke:#333,stroke-width:2px
    classDef externalClass fill:#FFB6C1,stroke:#333,stroke-width:2px
```
