"""Surface manipulation."""
from ..surface import SDL_CreateRGBSurfaceFrom

__all__ = ["subsurface"]

def subsurface(surface, area):
    """Creates a surface from a part of another surface.

    The two surfaces share pixel data. The subsurface *must not* be used after
    its parent has been freed!
    """
    surface_format = surface.format[0]
    subpixels = (surface.pixels + surface.pitch*area[1] +
                 surface_format.BytesPerPixel*area[0])
    return SDL_CreateRGBSurfaceFrom(subpixels, area[2], area[3],
                                    surface_format.BitsPerPixel,
                                    surface.pitch, surface_format.Rmask,
                                    surface_format.Gmask, surface_format.Bmask,
                                    surface_format.Amask)[0]
