# DEPRECATED WINDOWS-ONLY MODULES

This directory contains Windows-specific modules that have been **DEPRECATED** 
and replaced with Linux-native alternatives.

## ⚠️ DO NOT USE THESE MODULES IN NEW CODE

These modules are kept for reference only and will be removed in a future release.

## Deprecated Modules

### `dill/` - DirectInput Low-Level Library (Windows)
**Status:** DEPRECATED  
**Replacement:** Use `linput` (Linux Input) module  
**Reason:** Windows-specific DirectInput wrapper using ctypes.wintypes

**Migration:**
```python
# OLD (Windows):
import dill
from dill import GUID
guid = dill.GUID_Keyboard
device = dill.DILL.get_device_information_by_guid(guid)

# NEW (Linux):
import linput
guid = linput.GUID_Keyboard  # uuid.UUID
device = linput.DeviceManager().get_device_by_guid(guid)
```

**Compatibility Layer:** `dill_compat.py` in project root provides temporary 
backwards compatibility but will also be removed.

---

### `vjoy/` - Virtual Joystick (Windows vJoy)
**Status:** DEPRECATED  
**Replacement:** Use `linput.VirtualJoystick` (Linux uinput)  
**Reason:** Windows-specific vJoy driver wrapper

**Migration:**
```python
# OLD (Windows):
from vjoy.vjoy import VJoyProxy
vjoy = VJoyProxy()
device = vjoy.vjoy_devices[1]
device.axis(1).value = 0.5
device.button(3).is_pressed = True

# NEW (Linux):
import linput
device = linput.VirtualJoystick.get(1)
device.set_axis(1, 0.5)
device.set_button(3, True)
```

---

## Timeline

- **October 2025:** Modules moved to `deprecated_windows_only/`
- **November 2025:** All imports updated to use Linux alternatives
- **December 2025:** Remove deprecated modules and compatibility layer

---

## See Also

- **Linux Replacement Modules:**
  - `linput/` - Linux input/output handling
  - `gremlin/linux_process_monitor.py` - Process monitoring with psutil
  - `gremlin/linux_tts.py` - Text-to-speech with espeak-ng

- **Documentation:**
  - `REFACTORING_PLAN.md` - Complete refactoring roadmap
  - `LINUX_INTEGRATION_COMPLETE.md` - Linux port documentation
  - `ARCHITECTURE_VISUALIZATION.md` - Architecture diagrams

---

## For Developers

If you're maintaining old code that still uses these modules:

1. Update imports to use `linput` instead of `dill` or `vjoy`
2. Use `uuid.UUID` instead of `dill.GUID`  
3. Use `linput.VirtualJoystick` instead of `vjoy.VJoyProxy`
4. Test on a Linux system with real hardware

**Need help migrating?** See `REFACTORING_PLAN.md` for detailed examples.
