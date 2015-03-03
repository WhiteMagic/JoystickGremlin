from ctypes import c_char, c_char_p, POINTER
from .dll import _bind, nullfunc

__all__ = ["SDL_GetBasePath", "SDL_GetPrefPath"]

# The filesystem API came in after the 2.0 release
SDL_GetBasePath = _bind("SDL_GetBasePath", None, POINTER(c_char), nullfunc)
SDL_GetPrefPath = _bind("SDL_GetPrefPath", [c_char_p, c_char_p], POINTER(c_char),
                        nullfunc)
