"""Drawing routines for software surfaces."""
import ctypes
from .compat import isiterable, UnsupportedError
from .array import to_ctypes
from .color import convert_to_color
from .. import surface, pixels, rect
from .algorithms import clipline
from .sprite import SoftwareSprite

__all__ = ["prepare_color", "fill", "line"]


def _get_target_surface(target):
    """Gets the SDL_surface from the passed target."""
    if isinstance(target, surface.SDL_Surface):
        rtarget = target
    elif isinstance(target, SoftwareSprite):
        rtarget = target.surface
    else:
        raise TypeError("unsupported target type")
    return rtarget


def prepare_color(color, target):
    """Prepares the passed color for the passed target."""
    color = convert_to_color(color)
    pformat = None
    # Software surfaces
    if isinstance(target, pixels.SDL_PixelFormat):
        pformat = target
    elif isinstance(target, surface.SDL_Surface):
        pformat = target.format.contents
    elif isinstance(target, SoftwareSprite):
        pformat = target.surface.format.contents
    if pformat is None:
        raise TypeError("unsupported target type")
    if pformat.Amask != 0:
        # Target has an alpha mask
        return pixels.SDL_MapRGBA(pformat, color.r, color.g, color.b, color.a)
    return pixels.SDL_MapRGB(pformat, color.r, color.g, color.b)


def fill(target, color, area=None):
    """Fills a certain rectangular area on the passed target with a color.

    If no area is provided, the entire target will be filled with
    the passed color. If an iterable item is provided as area (such as a list
    or tuple), it will be first checked, if the item denotes a single
    rectangular area (4 integer values) before assuming it to be a sequence
    of rectangular areas.
    """
    color = prepare_color(color, target)
    rtarget = _get_target_surface(target)

    varea = None
    if area is not None and isiterable(area):
        # can be either a single rect or a list of rects)
        if len(area) == 4:
            # is it a rect?
            try:
                varea = rect.SDL_Rect(int(area[0]), int(area[1]),
                                      int(area[2]), int(area[3]))
            except:
                # No, not a rect, assume a seq of rects.
                pass
        if not varea:  # len(area) == 4 AND varea set.
            varea = []
            for r in area:
                varea.append(rect.SDL_Rect(r[0], r[1], r[2], r[3]))

    if varea is None or isinstance(varea, rect.SDL_Rect):
        surface.SDL_FillRect(rtarget, varea, color)
    else:
        varea, count = to_ctypes(varea, rect.SDL_Rect)
        varea = ctypes.cast(varea, ctypes.POINTER(rect.SDL_Rect))
        surface.SDL_FillRects(rtarget, varea, count, color)


def line(target, color, dline, width=1):
    """Draws one or multiple lines on the passed target.

    dline can be a sequence of four integers for a single line in the
    form (x1, y1, x2, y2) or a sequence of a multiple of 4 for drawing
    multiple lines at once, e.g. (x1, y1, x2, y2, x3, y3, x4, y4, ...).
    """
    if width < 1:
        raise ValueError("width must be greater than 0")
    color = prepare_color(color, target)
    rtarget = _get_target_surface(target)

    # line: (x1, y1, x2, y2) OR (x1, y1, x2, y2, ...)
    if (len(dline) % 4) != 0:
        raise ValueError("line does not contain a valid set of points")
    pcount = len(dline)
    SDLRect = rect.SDL_Rect
    fillrect = surface.SDL_FillRect

    pitch = rtarget.pitch
    bpp = rtarget.format.contents.BytesPerPixel
    frac = pitch / bpp
    clip_rect = rtarget.clip_rect
    left, right = clip_rect.x, clip_rect.x + clip_rect.w - 1
    top, bottom = clip_rect.y, clip_rect.y + clip_rect.h - 1

    if bpp == 3:
        raise UnsupportedError(line, "24bpp are currently not supported")
    if bpp == 2:
        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint16))
    elif bpp == 4:
        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint32))
    else:
        pxbuf = rtarget.pixels  # byte-wise access.

    for idx in range(0, pcount, 4):
        x1, y1, x2, y2 = dline[idx:idx + 4]
        if x1 == x2:
            # Vertical line
            if y1 < y2:
                varea = SDLRect(x1 - width // 2, y1, width, y2 - y1)
            else:
                varea = SDLRect(x1 - width // 2, y2, width, y1 - y2)
            fillrect(rtarget, varea, color)
            continue
        if y1 == y2:
            # Horizontal line
            if x1 < x2:
                varea = SDLRect(x1, y1 - width // 2, x2 - x1, width)
            else:
                varea = SDLRect(x2, y1 - width // 2, x1 - x2, width)
            fillrect(rtarget, varea, color)
            continue
        if width != 1:
            raise UnsupportedError(line, "width > 1 is not supported")
        if width == 1:
            # Bresenham
            x1, y1, x2, y2 = clipline(left, top, right, bottom, x1, y1, x2, y2)
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            if x1 is None:
                # not to be drawn
                continue
            dx = abs(x2 - x1)
            dy = -abs(y2 - y1)
            err = dx + dy
            sx, sy = 1, 1
            if x1 > x2:
                sx = -sx
            if y1 > y2:
                sy = -sy
            while True:
                pxbuf[int(y1 * frac + x1)] = color
                if x1 == x2 and y1 == y2:
                    break
                e2 = err * 2
                if e2 > dy:
                    err += dy
                    x1 += sx
                if e2 < dx:
                    err += dx
                    y1 += sy
