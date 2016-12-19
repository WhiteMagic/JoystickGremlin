from ctypes import c_int
from .dll import _bind, nullfunc
from .stdinc import SDL_bool

__all__ = ["SDL_CACHELINE_SIZE", "SDL_GetCPUCount", "SDL_GetCPUCacheLineSize",
           "SDL_HasRDTSC", "SDL_HasAltiVec", "SDL_HasMMX", "SDL_Has3DNow",
           "SDL_HasSSE", "SDL_HasSSE2", "SDL_HasSSE3", "SDL_HasSSE41",
           "SDL_HasSSE42", "SDL_GetSystemRAM", "SDL_HasAVX", "SDL_HasAVX2"
           ]

SDL_CACHELINE_SIZE = 128
SDL_GetCPUCount = _bind("SDL_GetCPUCount", None, c_int)
SDL_GetCPUCacheLineSize = _bind("SDL_GetCPUCacheLineSize", None, c_int)
SDL_HasRDTSC = _bind("SDL_HasRDTSC", None, SDL_bool)
SDL_HasAltiVec = _bind("SDL_HasAltiVec", None, SDL_bool)
SDL_HasMMX = _bind("SDL_HasMMX", None, SDL_bool)
SDL_Has3DNow = _bind("SDL_Has3DNow", None, SDL_bool)
SDL_HasSSE = _bind("SDL_HasSSE", None, SDL_bool)
SDL_HasSSE2 = _bind("SDL_HasSSE2", None, SDL_bool)
SDL_HasSSE3 = _bind("SDL_HasSSE3", None, SDL_bool)
SDL_HasSSE41 = _bind("SDL_HasSSE41", None, SDL_bool)
SDL_HasSSE42 = _bind("SDL_HasSSE42", None, SDL_bool)
SDL_GetSystemRAM = _bind("SDL_GetSystemRAM", None, c_int, nullfunc)
SDL_HasAVX = _bind("SDL_HasAVX", None, SDL_bool, nullfunc)
SDL_HasAVX2 = _bind("SDL_HasAVX2", None, SDL_bool, nullfunc)

