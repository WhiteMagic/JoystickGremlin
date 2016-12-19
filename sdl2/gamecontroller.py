from ctypes import Structure, Union, c_int, c_char_p, POINTER
from .dll import _bind, nullfunc
from .stdinc import SDL_bool, Sint16, Uint8
from .joystick import SDL_JoystickGUID, SDL_Joystick, SDL_JoystickID
from .rwops import SDL_RWops, SDL_RWFromFile


__all__ = ["SDL_GameController", "SDL_CONTROLLER_BINDTYPE_NONE",
           "SDL_CONTROLLER_BINDTYPE_BUTTON", "SDL_CONTROLLER_BINDTYPE_AXIS",
           "SDL_CONTROLLER_BINDTYPE_HAT", "SDL_GameControllerBindType",
           "SDL_GameControllerButtonBind", "SDL_GameControllerAddMapping",
           "SDL_GameControllerMappingForGUID", "SDL_GameControllerMapping",
           "SDL_IsGameController", "SDL_GameControllerNameForIndex",
           "SDL_GameControllerOpen", "SDL_GameControllerName",
           "SDL_GameControllerGetAttached", "SDL_GameControllerGetJoystick",
           "SDL_GameControllerEventState", "SDL_GameControllerUpdate",
           "SDL_CONTROLLER_AXIS_INVALID", "SDL_CONTROLLER_AXIS_LEFTX",
           "SDL_CONTROLLER_AXIS_LEFTY", "SDL_CONTROLLER_AXIS_RIGHTX",
           "SDL_CONTROLLER_AXIS_RIGHTY", "SDL_CONTROLLER_AXIS_TRIGGERLEFT",
           "SDL_CONTROLLER_AXIS_TRIGGERRIGHT", "SDL_CONTROLLER_AXIS_MAX",
           "SDL_GameControllerAxis", "SDL_GameControllerGetAxisFromString",
           "SDL_GameControllerGetStringForAxis",
           "SDL_GameControllerGetBindForAxis", "SDL_GameControllerGetAxis",
           "SDL_CONTROLLER_BUTTON_INVALID", "SDL_CONTROLLER_BUTTON_A",
           "SDL_CONTROLLER_BUTTON_B", "SDL_CONTROLLER_BUTTON_X",
           "SDL_CONTROLLER_BUTTON_Y", "SDL_CONTROLLER_BUTTON_BACK",
           "SDL_CONTROLLER_BUTTON_GUIDE", "SDL_CONTROLLER_BUTTON_START",
           "SDL_CONTROLLER_BUTTON_LEFTSTICK", "SDL_CONTROLLER_BUTTON_RIGHTSTICK",
           "SDL_CONTROLLER_BUTTON_LEFTSHOULDER",
           "SDL_CONTROLLER_BUTTON_RIGHTSHOULDER",
           "SDL_CONTROLLER_BUTTON_DPAD_UP", "SDL_CONTROLLER_BUTTON_DPAD_DOWN",
           "SDL_CONTROLLER_BUTTON_DPAD_LEFT", "SDL_CONTROLLER_BUTTON_DPAD_RIGHT",
           "SDL_CONTROLLER_BUTTON_MAX", "SDL_GameControllerButton",
           "SDL_GameControllerGetButtonFromString",
           "SDL_GameControllerGetStringForButton",
           "SDL_GameControllerGetBindForButton", "SDL_GameControllerGetButton",
           "SDL_GameControllerClose", "SDL_GameControllerAddMappingsFromFile",
           "SDL_GameControllerAddMappingsFromRW",
           "SDL_GameControllerFromInstanceID",
           ]

class SDL_GameController(Structure):
    pass

SDL_CONTROLLER_BINDTYPE_NONE = 0
SDL_CONTROLLER_BINDTYPE_BUTTON = 1
SDL_CONTROLLER_BINDTYPE_AXIS = 2
SDL_CONTROLLER_BINDTYPE_HAT = 3
SDL_GameControllerBindType = c_int

class _gchat(Structure):
    _fields_ = [("hat", c_int), ("hat_mask", c_int)]

class _gcvalue(Union):
    _fields_ = [("button", c_int), ("axis", c_int), ("hat", _gchat)]

class SDL_GameControllerButtonBind(Structure):
    _fields_ = [("bindType", SDL_GameControllerBindType), ("value", _gcvalue)]

SDL_GameControllerAddMapping = _bind("SDL_GameControllerAddMapping", [c_char_p], c_int)
SDL_GameControllerMappingForGUID = _bind("SDL_GameControllerMappingForGUID", [SDL_JoystickGUID], c_char_p)
SDL_GameControllerMapping = _bind("SDL_GameControllerMapping", [POINTER(SDL_GameController)], c_char_p)
SDL_IsGameController = _bind("SDL_IsGameController", [c_int], SDL_bool)
SDL_GameControllerNameForIndex = _bind("SDL_GameControllerNameForIndex", [c_int], c_char_p)
SDL_GameControllerOpen = _bind("SDL_GameControllerOpen", [c_int], POINTER(SDL_GameController))
SDL_GameControllerName = _bind("SDL_GameControllerName", [POINTER(SDL_GameController)], c_char_p)
SDL_GameControllerGetAttached = _bind("SDL_GameControllerGetAttached", [POINTER(SDL_GameController)], SDL_bool)
SDL_GameControllerGetJoystick = _bind("SDL_GameControllerGetJoystick", [POINTER(SDL_GameController)], POINTER(SDL_Joystick))
SDL_GameControllerEventState = _bind("SDL_GameControllerEventState", [c_int], c_int)
SDL_GameControllerUpdate = _bind("SDL_GameControllerUpdate")
SDL_CONTROLLER_AXIS_INVALID = -1
SDL_CONTROLLER_AXIS_LEFTX = 0
SDL_CONTROLLER_AXIS_LEFTY = 1
SDL_CONTROLLER_AXIS_RIGHTX = 2
SDL_CONTROLLER_AXIS_RIGHTY = 3
SDL_CONTROLLER_AXIS_TRIGGERLEFT = 4
SDL_CONTROLLER_AXIS_TRIGGERRIGHT = 5
SDL_CONTROLLER_AXIS_MAX = 6
SDL_GameControllerAxis = c_int
SDL_GameControllerGetAxisFromString = _bind("SDL_GameControllerGetAxisFromString", [c_char_p], SDL_GameControllerAxis)
SDL_GameControllerGetStringForAxis = _bind("SDL_GameControllerGetStringForAxis", [SDL_GameControllerAxis], c_char_p)
SDL_GameControllerGetBindForAxis = _bind("SDL_GameControllerGetBindForAxis", [POINTER(SDL_GameController), SDL_GameControllerAxis], SDL_GameControllerButtonBind)
SDL_GameControllerGetAxis = _bind("SDL_GameControllerGetAxis", [POINTER(SDL_GameController), SDL_GameControllerAxis], Sint16)
SDL_CONTROLLER_BUTTON_INVALID = -1
SDL_CONTROLLER_BUTTON_A = 0
SDL_CONTROLLER_BUTTON_B = 1
SDL_CONTROLLER_BUTTON_X = 2
SDL_CONTROLLER_BUTTON_Y = 3
SDL_CONTROLLER_BUTTON_BACK = 4
SDL_CONTROLLER_BUTTON_GUIDE = 5
SDL_CONTROLLER_BUTTON_START = 6
SDL_CONTROLLER_BUTTON_LEFTSTICK = 7
SDL_CONTROLLER_BUTTON_RIGHTSTICK = 8
SDL_CONTROLLER_BUTTON_LEFTSHOULDER = 9
SDL_CONTROLLER_BUTTON_RIGHTSHOULDER = 10
SDL_CONTROLLER_BUTTON_DPAD_UP = 11
SDL_CONTROLLER_BUTTON_DPAD_DOWN = 12
SDL_CONTROLLER_BUTTON_DPAD_LEFT = 13
SDL_CONTROLLER_BUTTON_DPAD_RIGHT = 14
SDL_CONTROLLER_BUTTON_MAX = 15
SDL_GameControllerButton = c_int
SDL_GameControllerGetButtonFromString = _bind("SDL_GameControllerGetButtonFromString", [c_char_p], SDL_GameControllerButton)
SDL_GameControllerGetStringForButton = _bind("SDL_GameControllerGetStringForButton", [SDL_GameControllerButton], c_char_p)
SDL_GameControllerGetBindForButton = _bind("SDL_GameControllerGetBindForButton", [POINTER(SDL_GameController), SDL_GameControllerButton], SDL_GameControllerButtonBind)
SDL_GameControllerGetButton = _bind("SDL_GameControllerGetButton", [POINTER(SDL_GameController), SDL_GameControllerButton], Uint8)
SDL_GameControllerClose = _bind("SDL_GameControllerClose", [POINTER(SDL_GameController)])
SDL_GameControllerAddMappingsFromRW = _bind("SDL_GameControllerAddMappingsFromRW", [POINTER(SDL_RWops), c_int], c_int, nullfunc)
SDL_GameControllerAddMappingsFromFile = lambda fname: SDL_GameControllerAddMappingsFromRW(SDL_RWFromFile(fname, b"rb"), 1)
SDL_GameControllerFromInstanceID = _bind("SDL_GameControllerFromInstanceID", [SDL_JoystickID], POINTER(SDL_GameController), nullfunc)

