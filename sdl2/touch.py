from ctypes import Structure, POINTER, c_float, c_int
from .dll import _bind
from .stdinc import Sint64

__all__ = ["SDL_TouchID", "SDL_FingerID", "SDL_Finger", "SDL_GetNumTouchDevices",
           "SDL_GetTouchDevice", "SDL_GetNumTouchFingers", "SDL_GetTouchFinger"
           ]

SDL_TouchID = Sint64
SDL_FingerID = Sint64

class SDL_Finger(Structure):
    _fields_ = [("id", SDL_FingerID),
                ("x", c_float),
                ("y", c_float),
                ("pressure", c_float)
                ]

# TODO: #define SDL_TOUCH_MOUSEID ((Uint32)-1)

SDL_GetNumTouchDevices = _bind("SDL_GetNumTouchDevices", None, c_int)
SDL_GetTouchDevice = _bind("SDL_GetTouchDevice", [c_int], SDL_TouchID)
SDL_GetNumTouchFingers = _bind("SDL_GetNumTouchFingers", [SDL_TouchID], c_int)
SDL_GetTouchFinger = _bind("SDL_GetTouchFinger", [SDL_TouchID, c_int], POINTER(SDL_Finger))
