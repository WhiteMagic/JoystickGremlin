"""Font and text rendering routines."""
import os
from .. import surface, rect, pixels
from .common import SDLError
from .compat import *
from .sprite import SoftwareSprite
from .color import Color, convert_to_color

_HASSDLTTF = True
try:
    from .. import sdlttf
except ImportError:
    _HASSDLTTF = False


__all__ = ["BitmapFont", "FontManager"]


class BitmapFont(object):
    """A bitmap graphics to character mapping.

    The BitmapFont class uses an image surface to find and render font
    character glyphs for text. It requires a mapping table, which
    denotes the characters available on the image.

    The mapping table is a list of strings, where each string reflects a
    'line' of characters on the image. Each character within each line
    has the same size as specified by the size argument.

    A typical mapping table might look like

      [ '0123456789',
        'ABCDEFGHIJ',
        'KLMNOPQRST',
        'UVWXYZ    ',
        'abcdefghij',
        'klmnopqrst',
        'uvwxyz    ',
        ',;.:!?+-()' ]
    """

    DEFAULTMAP = ["0123456789",
                  "ABCDEFGHIJ",
                  "KLMNOPQRST",
                  "UVWXYZ    ",
                  "abcdefghij",
                  "klmnopqrst",
                  "uvwxyz    ",
                  ",;.:!?+-()"
                ]


    def __init__(self, imgsurface, size, mapping=None):
        """Creates a new BitmapFont instance from the passed image.

        Each character is expected to be of the same size (a 2-value tuple
        denoting the width and height) and to be in order of the passed
        mapping.
        """
        if mapping is None:
            self.mapping = list(BitmapFont.DEFAULTMAP)
        else:
            self.mapping = mapping
        self.offsets = {}
        if isinstance(imgsurface, SoftwareSprite):
            self.surface = imgsurface.surface
        # elif isinstance(surface, sprite.Sprite):

        #    TODO
        elif isinstance(imgsurface, surface.SDL_Surface):
            self.surface = imgsurface
        self.size = size[0], size[1]
        self._calculate_offsets()

    def _calculate_offsets(self):
        """Calculates the internal character offsets for each line."""
        self.offsets = {}
        offsets = self.offsets
        x, y = 0, 0
        w, h = self.size
        for line in self.mapping:
            x = 0
            for c in line:
                offsets[c] = rect.SDL_Rect(x, y, w, h)
                x += w
            y += h

    def render(self, text, bpp=None):
        """Renders the passed text on a new Sprite and returns it."""
        tw, th = 0, 0
        w, h = self.size
        # TODO
        lines = text.split(os.linesep)
        for line in lines:
            tw = max(tw, sum([w for c in line]))
            th += h

        if bpp is None:
            bpp = self.surface.format.contents.BitsPerPixel
        sf = surface.SDL_CreateRGBSurface(0, tw, th, bpp, 0, 0, 0, 0)
        sf = sf.contents
        imgsurface = SoftwareSprite(sf, False)
        target = imgsurface.surface
        blit_surface = surface.SDL_BlitSurface
        fontsf = self.surface
        offsets = self.offsets

        dstr = rect.SDL_Rect(0, 0, 0, 0)
        y = 0
        for line in lines:
            dstr.y = y
            x = 0
            for c in line:
                dstr.x = x
                if c in offsets:
                    blit_surface(fontsf, offsets[c], target, dstr)
                # elif c != ' ':

                #    TODO: raise an exception for unknown char?
                x += w
            y += h
        return imgsurface

    def render_on(self, imgsurface, text, offset=(0, 0)):
        """Renders a text on the passed sprite, starting at a specific
        offset.

        The top-left start position of the text will be the passed offset and
        4-value tuple with the changed area will be returned.
        """
        w, h = self.size

        target = None
        if isinstance(imgsurface, SoftwareSprite):
            target = imgsurface.surface
        # elif isinstance(surface, sprite.Sprite):

        #    TODO
        elif isinstance(imgsurface, surface.SDL_Surface):
            target = imgsurface
        else:
            raise TypeError("unsupported surface type")

        lines = text.split(os.linesep)
        blit_surface = surface.SDL_BlitSurface
        fontsf = self.surface
        offsets = self.offsets

        dstr = rect.SDL_Rect(0, 0, 0, 0)
        y = offset[1]
        for line in lines:
            dstr.y = y
            x = offset[0]
            for c in line:
                dstr.x = x
                if c in offsets:
                    blit_surface(fontsf, offsets[c], target, dstr)
                # elif c != ' ':

                #    TODO: raise an exception for unknown char?
                x += w
            y += h
        return (offset[0], offset[1], x + w, y + h)

    def contains(self, c):
        """Checks, whether a certain character exists in the font."""
        return c == ' ' or c in self.offsets

    def can_render(self, text):
        """Checks, whether all characters in the passed text can be rendered.
        """
        lines = text.split(os.linesep)
        for line in lines:
            for c in line:
                if c != ' ' and c not in self.offsets:
                    return False
        return True


class FontManager(object):
    """Manage fonts and rendering of text."""
    def __init__(self, font_path, alias=None, size=16,
                 color=Color(255, 255, 255), bg_color=Color(0, 0, 0), index=0):
        """Initialize the FontManager

        One font path must be given to initialize the FontManager. The
        default_font will be set to this font. color and bg_color
        will give the FontManager a default color. size is the default
        font size in pixels.
        """
        if not _HASSDLTTF:
            raise UnsupportedError(FontManager,
                                   "FontManager requires sdlttf support")
        if sdlttf.TTF_WasInit() == 0 and sdlttf.TTF_Init() != 0:
            raise SDLError()
        self.fonts = {}  # fonts = {alias: {size:font_ptr}}
        self.aliases = {}  # aliases = {alias:font_path}
        self._textcolor = pixels.SDL_Color(0, 0, 0)
        self._bgcolor = pixels.SDL_Color(255, 255, 255)
        self.color = color
        self.bg_color = bg_color
        self.size = size
        self._default_font = self.add(font_path, alias, index)

    def __del__(self):
        """Close all opened fonts."""
        self.close()

    def close(self):
        """Close all opened fonts."""
        for alias, fonts in self.fonts.items():
            for size, font in fonts.items():
                if font:
                    sdlttf.TTF_CloseFont(font)
        self.fonts = {}
        self.aliases = {}

    def add(self, font_path, alias=None, size=None, index=0):
        """Add a font to the Font Manager.

        alias is by default the font name. But another name can be
        passed. Returns the font pointer stored in self.fonts.
        """
        size = size or self.size
        if alias is None:
            # If no alias given, take the font name as alias
            basename = os.path.basename(font_path)
            alias = os.path.splitext(basename)[0]
            if alias in self.fonts:
                if size in self.fonts[alias] and self.fonts[alias]:
                    # font with selected size already opened
                    return
                else:
                    self._change_font_size(alias, size)
                    return
            else:
                if not os.path.isfile(font_path):
                    raise IOError("Cannot find %s" % font_path)

        font = self._load_font(font_path, size, index)
        self.aliases[alias] = font_path
        self.fonts[alias] = {}
        self.fonts[alias][size] = font
        return font

    def _load_font(self, font_path, size, index=0):
        """Helper function to open the font.

        Raises an exception if something went wrong.
        """
        if index == 0:
            font = sdlttf.TTF_OpenFont(byteify(font_path, "utf-8"), size)
        else:
            font = sdlttf.TTF_OpenFontIndex(byteify(font_path, "utf-8"), size,
                                            index)
        if font is None:
            raise SDLError()
        return font

    def _change_font_size(self, alias, size):
        """Loads an already opened font in another size."""
        if alias not in self.fonts:
            raise KeyError("Font %s not loaded in FontManager" % alias)
        font = self._load_font(self.aliases[alias], size)
        self.fonts[alias][size] = font

    @property
    def color(self):
        """The text color to be used."""
        return Color(self._textcolor.r, self._textcolor.g, self._textcolor.b,
                     self._textcolor.a)

    @color.setter
    def color(self, value):
        """The text color to be used."""
        c = convert_to_color(value)
        self._textcolor = pixels.SDL_Color(c.r, c.g, c.b, c.a)

    @property
    def bg_color(self):
        """The background color to be used."""
        return Color(self._bgcolor.r, self._bgcolor.g, self._bgcolor.b,
                     self._bgcolor.a)

    @bg_color.setter
    def bg_color(self, value):
        """The background color to be used."""
        c = convert_to_color(value)
        self._bgcolor = pixels.SDL_Color(c.r, c.g, c.b, c.a)

    @property
    def default_font(self):
        """Returns the name of the current default_font."""
        for alias in self.fonts:
            for size, font in self.fonts[alias].items():
                if font == self._default_font:
                    return alias

    @default_font.setter
    def default_font(self, value):
        """value must be a font alias

        Set the default_font to the given font name alias,
        provided it's loaded in the font manager.
        """
        alias = value
        size = self.size
        if alias not in self.fonts:
            raise ValueError("Font %s not loaded in FontManager" % alias)
        # Check if size is already loaded, otherwise do it.
        if size not in self.fonts[alias]:
            self._change_font_size(alias, size)
            size = list(self.fonts[alias].keys())[0]
        self._default_font = self.fonts[alias][size]

    def render(self, text, alias=None, size=None, width=None, color=None,
               bg_color=None, **kwargs):
        """Renders text to a surface.

        This method uses the font designated by the alias or the
        default_font.  A size can be passed even if the font was not
        loaded with this size.  A width can be given for line wrapping.
        If no bg_color or color are given, it will default to the
        FontManager's bg_color and color.
        """
        alias = alias or self.default_font
        size = size or self.size
        if bg_color is None:
            bg_color = self._bgcolor
        elif not isinstance(bg_color, pixels.SDL_Color):
            c = convert_to_color(bg_color)
            bg_color = pixels.SDL_Color(c.r, c.g, c.b, c.a)
        if color is None:
            color = self._textcolor
        elif not isinstance(color, pixels.SDL_Color):
            c = convert_to_color(color)
            color = pixels.SDL_Color(c.r, c.g, c.b, c.a)
        if len(self.fonts) == 0:
            raise TypeError("There are no fonts selected.")
        font = self._default_font
        if alias not in self.aliases:
            raise KeyError("Font %s not loaded" % font)
        elif size not in self.fonts[alias]:
            self._change_font_size(alias, size)
        font = self.fonts[alias][size]
        text = byteify(text, "utf-8")
        if width:
            sf = sdlttf.TTF_RenderUTF8_Blended_Wrapped(font, text, color,
                                                       width)
        elif bg_color == pixels.SDL_Color(0, 0, 0):
            sf = sdlttf.TTF_RenderUTF8_Blended(font, text, color)
        else:
            sf = sdlttf.TTF_RenderUTF8_Shaded(font, text, color,
                                              bg_color)
        if not sf:
            raise SDLError(sdlttf.TTF_GetError())
        return sf.contents
