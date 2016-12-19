from ctypes import Union, Structure, c_int, c_void_p, c_long, c_ulong, \
    c_longlong, c_ulonglong, c_uint, sizeof, POINTER
from .dll import _bind
from .stdinc import SDL_bool, Uint32
from .version import SDL_version
from .video import SDL_Window

__all__ = ["SDL_SYSWM_TYPE", "SDL_SYSWM_UNKNOWN", "SDL_SYSWM_WINDOWS",
           "SDL_SYSWM_X11", "SDL_SYSWM_DIRECTFB", "SDL_SYSWM_COCOA",
           "SDL_SYSWM_UIKIT", "SDL_SYSWM_WAYLAND", "SDL_SYSWM_MIR",
           "SDL_SYSWM_WINRT", "SDL_SYSWM_ANDROID", "SDL_SYSWM_VIVANTE",
           "SDL_SysWMmsg", "SDL_SysWMinfo", "SDL_GetWindowWMInfo"
           ]

SDL_SYSWM_TYPE = c_int
SDL_SYSWM_UNKNOWN = 0
SDL_SYSWM_WINDOWS = 1
SDL_SYSWM_X11 = 2
SDL_SYSWM_DIRECTFB = 3
SDL_SYSWM_COCOA = 4
SDL_SYSWM_UIKIT = 5
SDL_SYSWM_WAYLAND = 6
SDL_SYSWM_MIR = 7
SDL_SYSWM_WINRT = 8
SDL_SYSWM_ANDROID = 9
SDL_SYSWM_VIVANTE = 10

# FIXME: Hack around the ctypes "_type_ 'v' not supported" bug - remove
# once this has been fixed properly in Python 2.7+
HWND = c_void_p
HDC = c_void_p
UINT = c_uint
if sizeof(c_long) == sizeof(c_void_p):
    WPARAM = c_ulong
    LPARAM = c_long
elif sizeof(c_longlong) == sizeof(c_void_p):
    WPARAM = c_ulonglong
    LPARAM = c_longlong
# FIXME: end

class _winmsg(Structure):
    _fields_ = [("hwnd", HWND),
                ("msg", UINT),
                ("wParam", WPARAM),
                ("lParam", LPARAM),
                ]


class _x11msg(Structure):
    _fields_ = [("event", c_void_p)]


class _dfbmsg(Structure):
    _fields_ = [("event", c_void_p)]


class _cocoamsg(Structure):
    pass


class _uikitmsg(Structure):
    pass


class _msg(Union):
    _fields_ = [("win", _winmsg),
                ("x11", _x11msg),
                ("dfb", _dfbmsg),
                ("cocoa", _cocoamsg),
                ("uikit", _uikitmsg),
                ("dummy", c_int)
                ]


class SDL_SysWMmsg(Structure):
    _fields_ = [("version", SDL_version),
                ("subsystem", SDL_SYSWM_TYPE),
                ("msg", _msg)
                ]


class _wininfo(Structure):
    _fields_ = [("window", HWND),
                ("hdc", HDC)]


class _winrtinfo(Structure):
    _fields_ = [("window", c_void_p)]


class _x11info(Structure):
    """Window information for X11."""
    _fields_ = [("display", c_void_p),
                ("window", c_ulong)]


class _dfbinfo(Structure):
    """Window information for DirectFB."""
    _fields_ = [("dfb", c_void_p),
                ("window", c_void_p),
                ("surface", c_void_p)]


class _cocoainfo(Structure):
    """Window information for MacOS X."""
    _fields_ = [("window", c_void_p)]


class _uikitinfo(Structure):
    """Window information for iOS."""
    _fields_ = [("window", c_void_p),
                ("framebuffer", Uint32),
                ("colorbuffer", Uint32),
                ("resolveFramebuffer", Uint32)]


class _wl(Structure):
    """Window information for Wayland."""
    _fields_ = [("display", c_void_p),
                ("surface", c_void_p),
                ("shell_surface", c_void_p)]


class _mir(Structure):
    """Window information for Mir."""
    _fields_ = [("connection", c_void_p),
                ("surface", c_void_p)]


class _android(Structure):
    """Window information for Android."""
    _fields_ = [("window", c_void_p),
                ("surface", c_void_p)]


class _vivante(Structure):
    """Window information for Vivante."""
    _fields_ = [("display", c_void_p),
                ("window", c_void_p)]

class _info(Union):
    """The platform-specific information of a window."""
    _fields_ = [("win", _wininfo),
                ("winrt", _winrtinfo),
                ("x11", _x11info),
                ("dfb", _dfbinfo),
                ("cocoa", _cocoainfo),
                ("uikit", _uikitinfo),
                ("wl", _wl),
                ("mir", _mir),
                ("android", _android),
                ("vivante", _vivante),
                ("dummy", c_int)
                ]


class SDL_SysWMinfo(Structure):
    """System-specific window manager information.

    This holds the low-level information about the window.
    """
    _fields_ = [("version", SDL_version),
                ("subsystem", SDL_SYSWM_TYPE),
                ("info", _info)
                ]

SDL_GetWindowWMInfo = _bind("SDL_GetWindowWMInfo", [POINTER(SDL_Window), POINTER(SDL_SysWMinfo)], SDL_bool)
