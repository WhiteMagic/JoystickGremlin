import os
from ctypes import Structure, POINTER, c_int, c_long, c_char_p
from .dll import DLL, nullfunc
from .version import SDL_version
from .rwops import SDL_RWops
from .stdinc import Uint16, Uint32
from .pixels import SDL_Color
from .surface import SDL_Surface
from .error import SDL_GetError, SDL_SetError

__all__ = ["get_dll_file", "SDL_TTF_MAJOR_VERSION", "SDL_TTF_MINOR_VERSION",
          "SDL_TTF_PATCHLEVEL", "SDL_TTF_VERSION", "TTF_MAJOR_VERSION",
          "TTF_MINOR_VERSION", "TTF_PATCHLEVEL", "TTF_VERSION",
          "TTF_Linked_Version", "UNICODE_BOM_NATIVE", "UNICODE_BOM_SWAPPED",
          "TTF_ByteSwappedUNICODE", "TTF_Font", "TTF_Init", "TTF_OpenFont",
          "TTF_OpenFontIndex", "TTF_OpenFontRW", "TTF_OpenFontIndexRW",
          "TTF_STYLE_NORMAL", "TTF_STYLE_BOLD", "TTF_STYLE_ITALIC",
          "TTF_STYLE_UNDERLINE", "TTF_STYLE_STRIKETHROUGH", "TTF_GetFontStyle",
          "TTF_SetFontStyle", "TTF_GetFontOutline", "TTF_SetFontOutline",
          "TTF_HINTING_NORMAL", "TTF_HINTING_LIGHT", "TTF_HINTING_MONO",
          "TTF_HINTING_NONE", "TTF_GetFontHinting", "TTF_SetFontHinting",
          "TTF_FontHeight", "TTF_FontAscent", "TTF_FontDescent",
          "TTF_FontLineSkip", "TTF_GetFontKerning", "TTF_SetFontKerning",
          "TTF_FontFaces", "TTF_FontFaceIsFixedWidth", "TTF_FontFaceFamilyName",
          "TTF_FontFaceStyleName", "TTF_GlyphIsProvided", "TTF_GlyphMetrics",
          "TTF_SizeText", "TTF_SizeUTF8", "TTF_SizeUNICODE",
          "TTF_RenderText_Solid", "TTF_RenderUTF8_Solid",
          "TTF_RenderUNICODE_Solid", "TTF_RenderGlyph_Solid",
          "TTF_RenderText_Shaded", "TTF_RenderUTF8_Shaded",
          "TTF_RenderUNICODE_Shaded", "TTF_RenderGlyph_Shaded",
          "TTF_RenderText_Blended", "TTF_RenderUTF8_Blended",
          "TTF_RenderUNICODE_Blended", "TTF_RenderText_Blended_Wrapped",
          "TTF_RenderUTF8_Blended_Wrapped", "TTF_RenderUNICODE_Blended_Wrapped",
          "TTF_RenderGlyph_Blended", "TTF_RenderText", "TTF_RenderUTF",
          "TTF_RenderUNICODE", "TTF_CloseFont", "TTF_Quit", "TTF_WasInit",
          "TTF_GetFontKerningSize", "TTF_GetFontKerningSizeGlyphs",
          "TTF_SetError", "TTF_GetError"
          ]

try:
    dll = DLL("SDL2_ttf", ["SDL2_ttf", "SDL2_ttf-2.0"],
              os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)

def get_dll_file():
    """Gets the file name of the loaded SDL2_ttf library."""
    return dll.libfile

_bind = dll.bind_function

SDL_TTF_MAJOR_VERSION = 2
SDL_TTF_MINOR_VERSION = 0
SDL_TTF_PATCHLEVEL = 14


def SDL_TTF_VERSION(x):
    x.major = SDL_TTF_MAJOR_VERSION
    x.minor = SDL_TTF_MINOR_VERSION
    x.patch = SDL_TTF_PATCHLEVEL

TTF_MAJOR_VERSION = SDL_TTF_MAJOR_VERSION
TTF_MINOR_VERSION = SDL_TTF_MINOR_VERSION
TTF_PATCHLEVEL = SDL_TTF_PATCHLEVEL
TTF_VERSION = SDL_TTF_VERSION

TTF_Linked_Version = _bind("TTF_Linked_Version", None, POINTER(SDL_version))
UNICODE_BOM_NATIVE = 0xFEFF
UNICODE_BOM_SWAPPED = 0xFFFE

TTF_ByteSwappedUNICODE = _bind("TTF_ByteSwappedUNICODE", [c_int])


class TTF_Font(Structure):
    pass

TTF_Init = _bind("TTF_Init", None, c_int)
TTF_OpenFont = _bind("TTF_OpenFont", [c_char_p, c_int], POINTER(TTF_Font))
TTF_OpenFontIndex = _bind("TTF_OpenFontIndex", [c_char_p, c_int, c_long], POINTER(TTF_Font))
TTF_OpenFontRW = _bind("TTF_OpenFontRW", [POINTER(SDL_RWops), c_int, c_int], POINTER(TTF_Font))
TTF_OpenFontIndexRW = _bind("TTF_OpenFontIndexRW", [POINTER(SDL_RWops), c_int, c_int, c_long], POINTER(TTF_Font))

TTF_STYLE_NORMAL = 0x00
TTF_STYLE_BOLD = 0x01
TTF_STYLE_ITALIC = 0x02
TTF_STYLE_UNDERLINE = 0x04
TTF_STYLE_STRIKETHROUGH = 0x08
TTF_GetFontStyle = _bind("TTF_GetFontStyle", [POINTER(TTF_Font)], c_int)
TTF_SetFontStyle = _bind("TTF_SetFontStyle", [POINTER(TTF_Font), c_int])
TTF_GetFontOutline = _bind("TTF_GetFontOutline", [POINTER(TTF_Font)], c_int)
TTF_SetFontOutline = _bind("TTF_SetFontOutline", [POINTER(TTF_Font), c_int])

TTF_HINTING_NORMAL = 0
TTF_HINTING_LIGHT = 1
TTF_HINTING_MONO = 2
TTF_HINTING_NONE = 3
TTF_GetFontHinting = _bind("TTF_GetFontHinting", [POINTER(TTF_Font)], c_int)
TTF_SetFontHinting = _bind("TTF_SetFontHinting", [POINTER(TTF_Font), c_int])

TTF_FontHeight = _bind("TTF_FontHeight", [POINTER(TTF_Font)], c_int)
TTF_FontAscent = _bind("TTF_FontAscent", [POINTER(TTF_Font)], c_int)
TTF_FontDescent = _bind("TTF_FontDescent", [POINTER(TTF_Font)], c_int)
TTF_FontLineSkip = _bind("TTF_FontLineSkip", [POINTER(TTF_Font)], c_int)
TTF_GetFontKerning = _bind("TTF_GetFontKerning", [POINTER(TTF_Font)], c_int)
TTF_SetFontKerning = _bind("TTF_SetFontKerning", [POINTER(TTF_Font), c_int])
TTF_FontFaces = _bind("TTF_FontFaces", [POINTER(TTF_Font)], c_long)
TTF_FontFaceIsFixedWidth = _bind("TTF_FontFaceIsFixedWidth", [POINTER(TTF_Font)], c_int)
TTF_FontFaceFamilyName = _bind("TTF_FontFaceFamilyName", [POINTER(TTF_Font)], c_char_p)
TTF_FontFaceStyleName = _bind("TTF_FontFaceStyleName", [POINTER(TTF_Font)], c_char_p)
TTF_GlyphIsProvided = _bind("TTF_GlyphIsProvided", [POINTER(TTF_Font), Uint16], c_int)
TTF_GlyphMetrics = _bind("TTF_GlyphMetrics", [POINTER(TTF_Font), Uint16, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)], c_int)
TTF_SizeText = _bind("TTF_SizeText", [POINTER(TTF_Font), c_char_p, POINTER(c_int), POINTER(c_int)], c_int)
TTF_SizeUTF8 = _bind("TTF_SizeUTF8", [POINTER(TTF_Font), c_char_p, POINTER(c_int), POINTER(c_int)], c_int)
TTF_SizeUNICODE = _bind("TTF_SizeUNICODE", [POINTER(TTF_Font), POINTER(Uint16), POINTER(c_int), POINTER(c_int)], c_int)
TTF_RenderText_Solid = _bind("TTF_RenderText_Solid", [POINTER(TTF_Font), c_char_p, SDL_Color], POINTER(SDL_Surface))
TTF_RenderUTF8_Solid = _bind("TTF_RenderUTF8_Solid", [POINTER(TTF_Font), c_char_p, SDL_Color], POINTER(SDL_Surface))
TTF_RenderUNICODE_Solid = _bind("TTF_RenderUNICODE_Solid", [POINTER(TTF_Font), POINTER(Uint16), SDL_Color], POINTER(SDL_Surface))
TTF_RenderGlyph_Solid = _bind("TTF_RenderGlyph_Solid", [POINTER(TTF_Font), Uint16, SDL_Color], POINTER(SDL_Surface))
TTF_RenderText_Shaded = _bind("TTF_RenderText_Shaded", [POINTER(TTF_Font), c_char_p, SDL_Color, SDL_Color], POINTER(SDL_Surface))
TTF_RenderUTF8_Shaded = _bind("TTF_RenderUTF8_Shaded", [POINTER(TTF_Font), c_char_p, SDL_Color, SDL_Color], POINTER(SDL_Surface))
TTF_RenderUNICODE_Shaded = _bind("TTF_RenderUNICODE_Shaded", [POINTER(TTF_Font), POINTER(Uint16), SDL_Color, SDL_Color], POINTER(SDL_Surface))
TTF_RenderGlyph_Shaded = _bind("TTF_RenderGlyph_Shaded", [POINTER(TTF_Font), Uint16, SDL_Color, SDL_Color], POINTER(SDL_Surface))
TTF_RenderText_Blended = _bind("TTF_RenderText_Blended", [POINTER(TTF_Font), c_char_p, SDL_Color], POINTER(SDL_Surface))
TTF_RenderUTF8_Blended = _bind("TTF_RenderUTF8_Blended", [POINTER(TTF_Font), c_char_p, SDL_Color], POINTER(SDL_Surface))
TTF_RenderUNICODE_Blended = _bind("TTF_RenderUNICODE_Blended", [POINTER(TTF_Font), POINTER(Uint16), SDL_Color], POINTER(SDL_Surface))
TTF_RenderText_Blended_Wrapped = _bind("TTF_RenderText_Blended_Wrapped", [POINTER(TTF_Font), c_char_p, SDL_Color, Uint32], POINTER(SDL_Surface))
TTF_RenderUTF8_Blended_Wrapped = _bind("TTF_RenderUTF8_Blended_Wrapped", [POINTER(TTF_Font), c_char_p, SDL_Color, Uint32], POINTER(SDL_Surface))
TTF_RenderUNICODE_Blended_Wrapped = _bind("TTF_RenderUNICODE_Blended_Wrapped", [POINTER(TTF_Font), POINTER(Uint16), SDL_Color, Uint32], POINTER(SDL_Surface))
TTF_RenderGlyph_Blended = _bind("TTF_RenderGlyph_Blended", [POINTER(TTF_Font), Uint16, SDL_Color], POINTER(SDL_Surface))
TTF_RenderText = TTF_RenderText_Shaded
TTF_RenderUTF = TTF_RenderUTF8_Shaded
TTF_RenderUNICODE = TTF_RenderUNICODE_Shaded
TTF_CloseFont = _bind("TTF_CloseFont", [POINTER(TTF_Font)])
TTF_Quit = _bind("TTF_Quit") 
TTF_WasInit = _bind("TTF_WasInit", None, c_int)
TTF_GetFontKerningSize = _bind("TTF_GetFontKerningSize", [POINTER(TTF_Font), c_int, c_int], c_int)
TTF_GetFontKerningSizeGlyphs = _bind("TTF_GetFontKerningSizeGlyphs", [POINTER(TTF_Font), Uint16, Uint16], c_int, nullfunc)
TTF_SetError = SDL_SetError
TTF_GetError = SDL_GetError

