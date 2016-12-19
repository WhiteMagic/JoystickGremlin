"""Sprite, texture and pixel surface routines."""
import abc
from ctypes import byref, cast, POINTER, c_int, c_float
from .common import SDLError
from .compat import *
from .color import convert_to_color
from .ebs import System
from .surface import subsurface
from .window import Window
from .image import load_image
from .. import blendmode, surface, rect, video, pixels, render, rwops
from ..stdinc import Uint8, Uint32

__all__ = ["Sprite", "SoftwareSprite", "TextureSprite", "SpriteFactory",
           "SoftwareSpriteRenderSystem", "SpriteRenderSystem",
           "TextureSpriteRenderSystem", "Renderer", "TEXTURE", "SOFTWARE"
          ]

TEXTURE = 0
SOFTWARE = 1


class Renderer(object):
    """SDL2-based renderer for windows and sprites."""
    def __init__(self, target, index=-1, logical_size=None,
                 flags=render.SDL_RENDERER_ACCELERATED):
        """Creates a new Renderer for the given target.

        If target is a Window or SDL_Window, index and flags are passed
        to the relevant sdl.render.create_renderer() call. If target is
        a SoftwareSprite or SDL_Surface, the index and flags arguments are
        ignored.
        """
        self.sdlrenderer = None
        self.rendertaget = None
        if isinstance(target, Window):
            self.sdlrenderer = render.SDL_CreateRenderer(target.window, index,
                                                         flags)
            self.rendertarget = target.window
        elif isinstance(target, video.SDL_Window):
            self.sdlrenderer = render.SDL_CreateRenderer(target, index, flags)
            self.rendertarget = target
        elif isinstance(target, SoftwareSprite):
            self.sdlrenderer = render.SDL_CreateSoftwareRenderer(target.surface)
            self.rendertarget = target.surface
        elif isinstance(target, surface.SDL_Surface):
            self.sdlrenderer = render.SDL_CreateSoftwareRenderer(target)
            self.rendertarget = target
        else:
            raise TypeError("unsupported target type")

        if logical_size is not None:
            self.logical_size = logical_size

    def __del__(self):
        if self.sdlrenderer:
            render.SDL_DestroyRenderer(self.sdlrenderer)
        self.rendertarget = None

    @property
    @deprecated
    def renderer(self):
        return self.sdlrenderer

    @property
    def logical_size(self):
        """The logical pixel size of the Renderer"""
        w, h = c_int(), c_int()
        render.SDL_RenderGetLogicalSize(self.sdlrenderer, byref(w), byref(h))
        return w.value, h.value

    @logical_size.setter
    def logical_size(self, size):
        """The logical pixel size of the Renderer"""
        width, height = size
        ret = render.SDL_RenderSetLogicalSize(self.sdlrenderer, width, height)
        if ret != 0:
            raise SDLError()

    @property
    def color(self):
        """The drawing color of the Renderer."""
        r, g, b, a = Uint8(), Uint8(), Uint8(), Uint8()
        ret = render.SDL_GetRenderDrawColor(self.sdlrenderer, byref(r), byref(g),
                                            byref(b), byref(a))
        if ret == -1:
            raise SDLError()
        return convert_to_color((r.value, g.value, b.value, a.value))

    @color.setter
    def color(self, value):
        """The drawing color of the Renderer."""
        c = convert_to_color(value)
        ret = render.SDL_SetRenderDrawColor(self.sdlrenderer, c.r, c.g, c.b, c.a)
        if ret == -1:
            raise SDLError()

    @property
    def blendmode(self):
        """The blend mode used for drawing operations (fill and line)."""
        mode = blendmode.SDL_BlendMode()
        ret = render.SDL_GetRenderDrawBlendMode(self.sdlrenderer, byref(mode))
        if ret == -1:
            raise SDLError()
        return mode

    @blendmode.setter
    def blendmode(self, value):
        """The blend mode used for drawing operations (fill and line)."""
        ret = render.SDL_SetRenderDrawBlendMode(self.sdlrenderer, value)
        if ret == -1:
            raise SDLError()

    @property
    def scale(self):
        """The horizontal and vertical drawing scale."""
        sx = c_float(0.0)
        sy = c_float(0.0)
        render.SDL_RenderGetScale(self.sdlrenderer, byref(sx), byref(sy))
        return sx.value, sy.value

    @scale.setter
    def scale(self, value):
        """The horizontal and vertical drawing scale."""
        ret = render.SDL_RenderSetScale(self.sdlrenderer, value[0], value[1])
        if ret != 0:
            raise SDLError()

    def clear(self, color=None):
        """Clears the renderer with the currently set or passed color."""
        if color is not None:
            tmp = self.color
            self.color = color
        ret = render.SDL_RenderClear(self.sdlrenderer)
        if color is not None:
            self.color = tmp
        if ret == -1:
            raise SDLError()

    def copy(self, src, srcrect=None, dstrect=None, angle=0, center=None,
             flip=render.SDL_FLIP_NONE):
        """Copies (blits) the passed source to the target of the Renderer."""
        if isinstance(src, TextureSprite):
            texture = src.texture
            angle = angle or src.angle
            center = center or src.center
            flip = flip or src.flip
        elif isinstance(src, render.SDL_Texture):
            texture = src
        else:
            raise TypeError("src must be a TextureSprite or SDL_Texture")
        if srcrect is not None:
            x, y, w, h = srcrect
            srcrect = rect.SDL_Rect(x, y, w, h)
        if dstrect is not None:
            x, y, w, h = dstrect
            dstrect = rect.SDL_Rect(x, y, w, h)
        ret = render.SDL_RenderCopyEx(self.sdlrenderer, texture, srcrect,
                                      dstrect, angle, center, flip)
        if ret == -1:
            raise SDLError()

    def present(self):
        """Refreshes the target of the Renderer."""
        render.SDL_RenderPresent(self.sdlrenderer)

    def draw_line(self, points, color=None):
        """Draws one or multiple connected lines on the renderer."""
        # (x1, y1, x2, y2, ...)
        pcount = len(points)
        if (pcount % 2) != 0:
            raise ValueError("points does not contain a valid set of points")
        if pcount < 4:
            raise ValueError("points must contain more that one point")
        if pcount == 4:
            if color is not None:
                tmp = self.color
                self.color = color
            x1, y1, x2, y2 = points
            ret = render.SDL_RenderDrawLine(self.sdlrenderer, x1, y1, x2, y2)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            off = 0
            count = pcount // 2
            SDL_Point = rect.SDL_Point
            ptlist = (SDL_Point * count)()
            while x < pcount:
                ptlist[off] = SDL_Point(points[x], points[x + 1])
                x += 2
                off += 1
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(ptlist, POINTER(SDL_Point))
            ret = render.SDL_RenderDrawLines(self.sdlrenderer, ptr, count)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()

    def draw_point(self, points, color=None):
        """Draws one or multiple points on the renderer."""
        # (x1, y1, x2, y2, ...)
        pcount = len(points)
        if (pcount % 2) != 0:
            raise ValueError("points does not contain a valid set of points")
        if pcount == 2:
            if color is not None:
                tmp = self.color
                self.color = color
            ret = render.SDL_RenderDrawPoint(self.sdlrenderer, points[0],
                                             points[1])
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            off = 0
            count = pcount // 2
            SDL_Point = rect.SDL_Point
            ptlist = (SDL_Point * count)()
            while x < pcount:
                ptlist[off] = SDL_Point(points[x], points[x + 1])
                x += 2
                off += 1
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(ptlist, POINTER(SDL_Point))
            ret = render.SDL_RenderDrawPoints(self.sdlrenderer, ptr, count)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()

    def draw_rect(self, rects, color=None):
        """Draws one or multiple rectangles on the renderer."""
        SDL_Rect = rect.SDL_Rect
        # ((x, y, w, h), ...)
        if type(rects[0]) == int:
            # single rect
            if color is not None:
                tmp = self.color
                self.color = color
            x, y, w, h = rects
            ret = render.SDL_RenderDrawRect(self.sdlrenderer, SDL_Rect(x, y, w, h))
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            rlist = (SDL_Rect * len(rects))()
            for idx, r in enumerate(rects):
                rlist[idx] = SDL_Rect(r[0], r[1], r[2], r[3])
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(rlist, POINTER(SDL_Rect))
            ret = render.SDL_RenderDrawRects(self.sdlrenderer, ptr, len(rects))
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()

    def fill(self, rects, color=None):
        """Fills one or multiple rectangular areas on the renderer."""
        SDL_Rect = rect.SDL_Rect
        # ((x, y, w, h), ...)
        if type(rects[0]) == int:
            # single rect
            if color is not None:
                tmp = self.color
                self.color = color
            x, y, w, h = rects
            ret = render.SDL_RenderFillRect(self.sdlrenderer, SDL_Rect(x, y, w, h))
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            rlist = (SDL_Rect * len(rects))()
            for idx, r in enumerate(rects):
                rlist[idx] = SDL_Rect(r[0], r[1], r[2], r[3])
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(rlist, POINTER(SDL_Rect))
            ret = render.SDL_RenderFillRects(self.sdlrenderer, ptr, len(rects))
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()



class Sprite(object):
    """A simple 2D object."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Creates a new Sprite."""
        super(Sprite, self).__init__()
        self.x = 0
        self.y = 0
        self.depth = 0

    @property
    def position(self):
        """The top-left position of the Sprite as tuple."""
        return self.x, self.y

    @position.setter
    def position(self, value):
        """The top-left position of the Sprite as tuple."""
        self.x = value[0]
        self.y = value[1]

    @property
    @abc.abstractmethod
    def size(self):
        """The size of the Sprite as tuple."""
        return

    @property
    def area(self):
        """The rectangular area occupied by the Sprite."""
        w, h = self.size
        return (self.x, self.y, self.x + w, self.y + h)


class SoftwareSprite(Sprite):
    """A simple, visible, pixel-based 2D object using software buffers."""
    def __init__(self, imgsurface, free):
        """Creates a new SoftwareSprite."""
        super(SoftwareSprite, self).__init__()
        self.free = free
        if not isinstance(imgsurface, surface.SDL_Surface):
            raise TypeError("surface must be a SDL_Surface")
        self.surface = imgsurface

    def __del__(self):
        """Releases the bound SDL_Surface, if it was created by the
        SoftwareSprite.
        """
        imgsurface = getattr(self, "surface", None)
        if self.free and imgsurface is not None:
            surface.SDL_FreeSurface(imgsurface)
        self.surface = None

    @property
    def size(self):
        """The size of the SoftwareSprite as tuple."""
        return self.surface.w, self.surface.h

    def subsprite(self, area):
        """Creates another SoftwareSprite from a part of the SoftwareSprite.

        The two sprites share pixel data, so if the parent sprite's surface is
        not managed by the sprite (free is False), you will need to keep it
        alive while the subsprite exists."""
        ssurface = subsurface(self.surface, area)
        ssprite = SoftwareSprite(ssurface, True)
        # Keeps the parent surface alive until subsprite is freed
        if self.free:
            ssprite._parent = self
        return ssprite

    def __repr__(self):
        return "SoftwareSprite(size=%s, bpp=%d)" % \
            (self.size, self.surface.format.contents.BitsPerPixel)


class TextureSprite(Sprite):
    """A simple, visible, texture-based 2D object, using a renderer."""
    def __init__(self, texture):
        """Creates a new TextureSprite."""
        super(TextureSprite, self).__init__()
        self.texture = texture
        flags = Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        ret = render.SDL_QueryTexture(texture, byref(flags), byref(access),
                                      byref(w), byref(h))
        if ret == -1:
            raise SDLError()
        self.angle = 0.0
        self.flip = render.SDL_FLIP_NONE
        self._size = w.value, h.value
        self._center = None

    def __del__(self):
        """Releases the bound SDL_Texture."""
        if self.texture is not None:
            render.SDL_DestroyTexture(self.texture)
        self.texture = None

    @property
    def center(self):
        """The center of the TextureSprite as tuple."""
        return self._center

    @center.setter
    def center(self, value):
        """Sets the center of the TextureSprite."""
        if value != None:
            self._center = rect.SDL_Point(value[0], value[1])
        else:
            self._center = None

    @property
    def size(self):
        """The size of the TextureSprite as tuple."""
        return self._size

    def __repr__(self):
        flags = Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        ret = render.SDL_QueryTexture(self.texture, byref(flags),
                                      byref(access), byref(w), byref(h))
        if ret == -1:
            raise SDLError()
        return "TextureSprite(format=%d, access=%d, size=%s, angle=%f, center=%s)" % \
            (flags.value, access.value, (w.value, h.value), self.angle,
             (self.center.x, self.center.y))


class SpriteFactory(object):
    """A factory class for creating Sprite components."""
    def __init__(self, sprite_type=TEXTURE, **kwargs):
        """Creates a new SpriteFactory.

        The SpriteFactory can create TextureSprite or SoftwareSprite
        instances, depending on the sprite_type being passed to it,
        which can be SOFTWARE or TEXTURE. The additional kwargs are used
        as default arguments for creating sprites within the factory
        methods.
        """
        if sprite_type == TEXTURE:
            if "renderer" not in kwargs:
                raise ValueError("you have to provide a renderer=<arg> argument")
        elif sprite_type != SOFTWARE:
            raise ValueError("sprite_type must be TEXTURE or SOFTWARE")
        self._spritetype = sprite_type
        self.default_args = kwargs

    @property
    def sprite_type(self):
        """The sprite type created by the factory."""
        return self._spritetype

    def __repr__(self):
        stype = "TEXTURE"
        if self.sprite_type == SOFTWARE:
            stype = "SOFTWARE"
        return "SpriteFactory(sprite_type=%s, default_args=%s)" % \
            (stype, self.default_args)

    def create_sprite_render_system(self, *args, **kwargs):
        """Creates a new SpriteRenderSystem.

        For TEXTURE mode, the passed args and kwargs are ignored and the
        Renderer or SDL_Renderer passed to the SpriteFactory is used.
        """
        if self.sprite_type == TEXTURE:
            return TextureSpriteRenderSystem(self.default_args["renderer"])
        else:
            return SoftwareSpriteRenderSystem(*args, **kwargs)

    def from_image(self, fname):
        """Creates a Sprite from the passed image file."""
        return self.from_surface(load_image(fname), True)

    def from_surface(self, tsurface, free=False):
        """Creates a Sprite from the passed SDL_Surface.

        If free is set to True, the passed surface will be freed
        automatically.
        """
        if self.sprite_type == TEXTURE:
            renderer = self.default_args["renderer"]
            texture = render.SDL_CreateTextureFromSurface(renderer.sdlrenderer,
                                                          tsurface)
            if not texture:
                raise SDLError()
            sprite = TextureSprite(texture.contents)
            if free:
                surface.SDL_FreeSurface(tsurface)
            return sprite
        elif self.sprite_type == SOFTWARE:
            return SoftwareSprite(tsurface, free)
        raise ValueError("sprite_type must be TEXTURE or SOFTWARE")

    def from_object(self, obj):
        """Creates a Sprite from an arbitrary object."""
        if self.sprite_type == TEXTURE:
            rw = rwops.rw_from_object(obj)
            # TODO: support arbitrary objects.
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise SDLError()
            return self.from_surface(imgsurface.contents, True)
        elif self.sprite_type == SOFTWARE:
            rw = rwops.rw_from_object(obj)
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise SDLError()
            return SoftwareSprite(imgsurface.contents, True)
        raise ValueError("sprite_type must be TEXTURE or SOFTWARE")

    def from_color(self, color, size, bpp=32, masks=None):
        """Creates a sprite with a certain color.
        """
        color = convert_to_color(color)
        if masks:
            rmask, gmask, bmask, amask = masks
        else:
            rmask = gmask = bmask = amask = 0
        sfc = surface.SDL_CreateRGBSurface(0, size[0], size[1], bpp, rmask,
                                           gmask, bmask, amask)
        if not sfc:
            raise SDLError()
        sfc = sfc.contents
        fmt = sfc.format.contents
        if fmt.Amask != 0:
            # Target has an alpha mask
            col = pixels.SDL_MapRGBA(fmt, color.r, color.g, color.b, color.a)
        else:
            col = pixels.SDL_MapRGB(fmt, color.r, color.g, color.b)
        ret = surface.SDL_FillRect(sfc, None, col)
        if ret == -1:
            raise SDLError()
        return self.from_surface(sfc, True)

    def from_text(self, text, **kwargs):
        """Creates a Sprite from a string of text."""
        args = self.default_args.copy()
        args.update(kwargs)
        fontmanager = args['fontmanager']
        sfc = fontmanager.render(text, **args)
        return self.from_surface(sfc, free=True)

    def create_sprite(self, **kwargs):
        """Creates an empty Sprite.

        This will invoke create_software_sprite() or
        create_texture_sprite() with the passed arguments and the set
        default arguments.
        """
        args = self.default_args.copy()
        args.update(kwargs)
        if self.sprite_type == TEXTURE:
            return self.create_texture_sprite(**args)
        else:
            return self.create_software_sprite(**args)

    def create_software_sprite(self, size, bpp=32, masks=None):
        """Creates a software sprite.

        A size tuple containing the width and height of the sprite and a
        bpp value, indicating the bits per pixel to be used, need to be
        provided.
        """
        if masks:
            rmask, gmask, bmask, amask = masks
        else:
            rmask = gmask = bmask = amask = 0
        imgsurface = surface.SDL_CreateRGBSurface(0, size[0], size[1], bpp,
                                                  rmask, gmask, bmask, amask)
        if not imgsurface:
            raise SDLError()
        return SoftwareSprite(imgsurface.contents, True)

    def create_texture_sprite(self, renderer, size,
                              pformat=pixels.SDL_PIXELFORMAT_RGBA8888,
                              access=render.SDL_TEXTUREACCESS_STATIC):
        """Creates a texture sprite.

        A size tuple containing the width and height of the sprite needs
        to be provided.

        TextureSprite objects are assumed to be static by default,
        making it impossible to access their pixel buffer in favour for
        faster copy operations. If you need to update the pixel data
        frequently or want to use the texture as target for rendering
        operations, access can be set to the relevant
        SDL_TEXTUREACCESS_* flag.
        """
        if isinstance(renderer, render.SDL_Renderer):
            sdlrenderer = renderer
        elif isinstance(renderer, Renderer):
            sdlrenderer = renderer.sdlrenderer
        else:
            raise TypeError("renderer must be a Renderer or SDL_Renderer")
        texture = render.SDL_CreateTexture(sdlrenderer, pformat, access,
                                           size[0], size[1])
        if not texture:
            raise SDLError()
        return TextureSprite(texture.contents)


class SpriteRenderSystem(System):
    """A rendering system for Sprite components.

    This is a base class for rendering systems capable of drawing and
    displaying Sprite-based objects. Inheriting classes need to
    implement the rendering capability by overriding the render()
    method.
    """
    def __init__(self):
        super(SpriteRenderSystem, self).__init__()
        self.componenttypes = (Sprite,)
        self._sortfunc = lambda e: e.depth

    def render(self, sprites, x=None, y=None):
        """Renders the passed sprites.

        This is a no-op function and needs to be implemented by inheriting
        classes.
        """
        pass

    def process(self, world, components):
        """Draws the passed SoftSprite objects on the Window's surface."""
        self.render(sorted(components, key=self._sortfunc))

    @property
    def sortfunc(self):
        """Sort function for the component processing order.

        The default sort order is based on the depth attribute of every
        sprite. Lower depth values will cause sprites to be drawn below
        sprites with higher depth values.
        """
        return self._sortfunc

    @sortfunc.setter
    def sortfunc(self, value):
        """Sort function for the component processing order.

        The default sort order is based on the depth attribute of every
        sprite. Lower depth values will cause sprites to be drawn below
        sprites with higher depth values.
        """
        if not callable(value):
            raise TypeError("sortfunc must be callable")
        self._sortfunc = value


class SoftwareSpriteRenderSystem(SpriteRenderSystem):
    """A rendering system for SoftwareSprite components.

    The SoftwareSpriteRenderSystem class uses a Window as drawing device to
    display Sprite surfaces. It uses the Window's internal SDL surface as
    drawing context, so that GL operations, such as texture handling or
    using SDL renderers is not possible.
    """
    def __init__(self, window):
        """Creates a new SoftwareSpriteRenderSystem for a specific Window."""
        super(SoftwareSpriteRenderSystem, self).__init__()
        if isinstance(window, Window):
            self.window = window.window
        elif isinstance(window, video.SDL_Window):
            self.window = window
        else:
            raise TypeError("unsupported window type")
        sfc = video.SDL_GetWindowSurface(self.window)
        if not sfc:
            raise SDLError()
        self.surface = sfc.contents
        self.componenttypes = (SoftwareSprite,)

    def render(self, sprites, x=None, y=None):
        """Draws the passed sprites (or sprite) on the Window's surface.

        x and y are optional arguments that can be used as relative drawing
        location for sprites. If set to None, the location information of the
        sprites are used. If set and sprites is an iterable, such as a list of
        SoftwareSprite objects, x and y are relative location values that will
        be added to each individual sprite's position. If sprites is a single
        SoftwareSprite, x and y denote the absolute position of the
        SoftwareSprite, if set.
        """
        r = rect.SDL_Rect(0, 0, 0, 0)
        if isiterable(sprites):
            blit_surface = surface.SDL_BlitSurface
            imgsurface = self.surface
            x = x or 0
            y = y or 0
            for sprite in sprites:
                r.x = x + sprite.x
                r.y = y + sprite.y
                blit_surface(sprite.surface, None, imgsurface, r)
        else:
            r.x = sprites.x
            r.y = sprites.y
            if x is not None and y is not None:
                r.x = x
                r.y = y
            surface.SDL_BlitSurface(sprites.surface, None, self.surface, r)
        video.SDL_UpdateWindowSurface(self.window)


class TextureSpriteRenderSystem(SpriteRenderSystem):
    """A rendering system for TextureSprite components.

    The TextureSpriteRenderSystem class uses a SDL_Renderer as drawing
    device to display TextureSprite objects.
    """
    def __init__(self, target):
        """Creates a new TextureSpriteRenderSystem.

        target can be a Window, SDL_Window, Renderer or SDL_Renderer.
        If it is a Window or SDL_Window instance, a Renderer will be
        created to acquire the SDL_Renderer.
        """
        super(TextureSpriteRenderSystem, self).__init__()
        if isinstance(target, (Window, video.SDL_Window)):
            # Create a Renderer for the window and use that one.
            target = Renderer(target)
        if isinstance(target, Renderer):
            self._renderer = target  # Used to prevent GC
            sdlrenderer = target.sdlrenderer
        elif isinstance(target, render.SDL_Renderer):
            sdlrenderer = target
        else:
            raise TypeError("unsupported object type")
        self.sdlrenderer = sdlrenderer
        self.componenttypes = (TextureSprite,)

    def render(self, sprites, x=None, y=None):
        """Draws the passed sprites (or sprite).

        x and y are optional arguments that can be used as relative
        drawing location for sprites. If set to None, the location
        information of the sprites are used. If set and sprites is an
        iterable, such as a list of TextureSprite objects, x and y are
        relative location values that will be added to each individual
        sprite's position. If sprites is a single TextureSprite, x and y
        denote the absolute position of the TextureSprite, if set.
        """
        r = rect.SDL_Rect(0, 0, 0, 0)
        rcopy = render.SDL_RenderCopyEx
        if isiterable(sprites):
            renderer = self.sdlrenderer
            x = x or 0
            y = y or 0
            for sprite in sprites:
                r.x = x + sprite.x
                r.y = y + sprite.y
                r.w, r.h = sprite.size
                if rcopy(renderer, sprite.texture, None, r, sprite.angle,
                         sprite.center, sprite.flip) == -1:
                    raise SDLError()
        else:
            r.x = sprites.x
            r.y = sprites.y
            r.w, r.h = sprites.size
            if x is not None and y is not None:
                r.x = x
                r.y = y
            if rcopy(self.sdlrenderer, sprites.texture, None, r, sprites.angle,
                     sprites.center, sprites.flip) == -1:
                raise SDLError()
        render.SDL_RenderPresent(self.sdlrenderer)
