import os
from ctypes import POINTER, c_int, c_char_p
from .dll import DLL
from .version import SDL_version
from .surface import SDL_Surface
from .rwops import SDL_RWops
from .render import SDL_Texture, SDL_Renderer
from .error import SDL_SetError, SDL_GetError

__all__ = ["SDL_IMAGE_MAJOR_VERSION", "SDL_IMAGE_MINOR_VERSION", \
           "SDL_IMAGE_PATCHLEVEL", "SDL_IMAGE_VERSION", "IMG_Linked_Version",
           "IMG_InitFlags", "IMG_INIT_JPG", "IMG_INIT_PNG", "IMG_INIT_TIF",
           "IMG_INIT_WEBP", "IMG_Init", "IMG_Quit", "IMG_LoadTyped_RW",
           "IMG_Load", "IMG_Load_RW", "IMG_LoadTexture", "IMG_LoadTexture_RW",
           "IMG_LoadTextureTyped_RW", "IMG_isICO", "IMG_isCUR", "IMG_isBMP",
           "IMG_isGIF", "IMG_isJPG", "IMG_isLBM", "IMG_isPNG", "IMG_isPNM",
           "IMG_isPCX", "IMG_isTIF", "IMG_isXCF", "IMG_isXV", "IMG_isWEBP",
           "IMG_LoadBMP_RW", "IMG_LoadCUR_RW", "IMG_LoadCUR_RW",
           "IMG_LoadGIF_RW", "IMG_LoadICO_RW", "IMG_LoadJPG_RW",
           "IMG_LoadLBM_RW", "IMG_LoadPCX_RW", "IMG_LoadPNM_RW",
           "IMG_LoadPNG_RW", "IMG_LoadTGA_RW", "IMG_LoadTIF_RW",
           "IMG_LoadXCF_RW", "IMG_LoadWEBP_RW", "IMG_LoadXPM_RW",
           "IMG_LoadXV_RW", "IMG_ReadXPMFromArray",
           "IMG_GetError", "IMG_SetError",
           "get_dll_file"
           ]

try:
    dll = DLL("SDL2_image", ["SDL2_image", "SDL2_image-2.0"],
              os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)


def get_dll_file():
    """Gets the file name of the loaded SDL2_image library."""
    return dll.libfile

_bind = dll.bind_function

SDL_IMAGE_MAJOR_VERSION = 2
SDL_IMAGE_MINOR_VERSION = 0
SDL_IMAGE_PATCHLEVEL = 0


def SDL_IMAGE_VERSION(x):
    x.major = SDL_IMAGE_MAJOR_VERSION
    x.minor = SDL_IMAGE_MINOR_VERSION
    x.patch = SDL_IMAGE_PATCHLEVEL

IMG_Linked_Version = _bind("IMG_Linked_Version", None, POINTER(SDL_version))

IMG_InitFlags = c_int
IMG_INIT_JPG = 0x00000001
IMG_INIT_PNG = 0x00000002
IMG_INIT_TIF = 0x00000004
IMG_INIT_WEBP = 0x00000008

IMG_Init = _bind("IMG_Init", [c_int], c_int)
IMG_Quit = _bind("IMG_Quit")
IMG_LoadTyped_RW = _bind("IMG_LoadTyped_RW", [POINTER(SDL_RWops), c_int, c_char_p], POINTER(SDL_Surface))
IMG_Load = _bind("IMG_Load", [c_char_p], POINTER(SDL_Surface))
IMG_Load_RW = _bind("IMG_Load_RW", [POINTER(SDL_RWops), c_int], POINTER(SDL_Surface))
IMG_LoadTexture = _bind("IMG_LoadTexture", [POINTER(SDL_Renderer), c_char_p], POINTER(SDL_Texture))
IMG_LoadTexture_RW = _bind("IMG_LoadTexture_RW", [POINTER(SDL_Renderer), POINTER(SDL_RWops), c_int], POINTER(SDL_Texture))
IMG_LoadTextureTyped_RW = _bind("IMG_LoadTextureTyped_RW", [POINTER(SDL_Renderer), POINTER(SDL_RWops), c_int, c_char_p], POINTER(SDL_Texture))

IMG_isICO = _bind("IMG_isICO", [POINTER(SDL_RWops)], c_int)
IMG_isCUR = _bind("IMG_isCUR", [POINTER(SDL_RWops)], c_int)
IMG_isBMP = _bind("IMG_isBMP", [POINTER(SDL_RWops)], c_int)
IMG_isGIF = _bind("IMG_isGIF", [POINTER(SDL_RWops)], c_int)
IMG_isJPG = _bind("IMG_isJPG", [POINTER(SDL_RWops)], c_int)
IMG_isLBM = _bind("IMG_isLBM", [POINTER(SDL_RWops)], c_int)
IMG_isPCX = _bind("IMG_isPCX", [POINTER(SDL_RWops)], c_int)
IMG_isPNG = _bind("IMG_isPNG", [POINTER(SDL_RWops)], c_int)
IMG_isPNM = _bind("IMG_isPNM", [POINTER(SDL_RWops)], c_int)
IMG_isTIF = _bind("IMG_isTIF", [POINTER(SDL_RWops)], c_int)
IMG_isXCF = _bind("IMG_isXCF", [POINTER(SDL_RWops)], c_int)
IMG_isXPM = _bind("IMG_isXPM", [POINTER(SDL_RWops)], c_int)
IMG_isXV = _bind("IMG_isXV", [POINTER(SDL_RWops)], c_int)
IMG_isWEBP = _bind("IMG_isWEBP", [POINTER(SDL_RWops)], c_int)

IMG_LoadICO_RW = _bind("IMG_LoadICO_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadCUR_RW = _bind("IMG_LoadCUR_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadBMP_RW = _bind("IMG_LoadBMP_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadGIF_RW = _bind("IMG_LoadGIF_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadJPG_RW = _bind("IMG_LoadJPG_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadLBM_RW = _bind("IMG_LoadLBM_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadPCX_RW = _bind("IMG_LoadPCX_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadPNG_RW = _bind("IMG_LoadPNG_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadPNM_RW = _bind("IMG_LoadPNM_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadTGA_RW = _bind("IMG_LoadTGA_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadTIF_RW = _bind("IMG_LoadTIF_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadXCF_RW = _bind("IMG_LoadXCF_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadXPM_RW = _bind("IMG_LoadXPM_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadXV_RW = _bind("IMG_LoadXV_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))
IMG_LoadWEBP_RW = _bind("IMG_LoadWEBP_RW", [POINTER(SDL_RWops)], POINTER(SDL_Surface))

IMG_ReadXPMFromArray = _bind("IMG_ReadXPMFromArray", [POINTER(c_char_p)], POINTER(SDL_Surface))

IMG_SavePNG = _bind("IMG_SavePNG", [POINTER(SDL_Surface), c_char_p], c_int)
IMG_SavePNG_RW = _bind("IMG_SavePNG_RW", [POINTER(SDL_Surface), POINTER(SDL_RWops), c_int], c_int)

IMG_SetError = SDL_SetError
IMG_GetError = SDL_GetError
