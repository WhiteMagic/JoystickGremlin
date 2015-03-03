"""Pixel-wise access routines."""
import ctypes
from .compat import UnsupportedError, experimental
from .array import MemoryView
from ..surface import SDL_MUSTLOCK, SDL_LockSurface, SDL_UnlockSurface, \
    SDL_Surface
from ..stdinc import Uint8
from .sprite import SoftwareSprite
from .draw import prepare_color


__all__ = ["PixelView", "pixels2d", "pixels3d"]


class PixelView(MemoryView):
    """2D memory view for Sprite and SDL_Surface pixel access.

    The PixelView uses a y/x-layout. Accessing view[N] will operate on the
    Nth row of the underlying surface. To access a specific column within
    that row, view[N][C] has to be used.

    NOTE: The PixelView is implemented on top of the MemoryView class. As such
    it makes heavy use of recursion to access rows and columns and can be
    considered as slow in contrast to optimised ndim-array solutions such as
    numpy.
    """
    def __init__(self, source):
        """Creates a new PixelView from a Sprite or SDL_Surface.

        If necessary, the surface will be locked for accessing its pixel data.
        The lock will be removed once the PixelView is garbage-collected or
        deleted.
        """
        if isinstance(source, SoftwareSprite):
            self._surface = source.surface
            # keep a reference, so the Sprite's not GC'd
            self._sprite = source
        elif isinstance(source, SDL_Surface):
            self._surface = source
        else:
            raise TypeError("source must be a Sprite or SDL_Surface")

        if SDL_MUSTLOCK(self._surface):
            SDL_LockSurface(self._surface)

        pxbuf = ctypes.cast(self._surface.pixels, ctypes.POINTER(Uint8))
        itemsize = self._surface.format.contents.BytesPerPixel
        strides = (self._surface.h, self._surface.w)
        srcsize = self._surface.h * self._surface.pitch
        super(PixelView, self).__init__(pxbuf, itemsize, strides,
                                        getfunc=self._getitem,
                                        setfunc=self._setitem,
                                        srcsize=srcsize)

    def _getitem(self, start, end):
        if self.itemsize == 1:
            # byte-wise access
            return self.source[start:end]
        # move the pointer to the correct location
        src = ctypes.byref(self.source.contents, start)
        casttype = ctypes.c_ubyte
        if self.itemsize == 2:
            casttype = ctypes.c_ushort
        elif self.itemsize == 3:
            # TODO
            raise NotImplementedError("unsupported bpp")
        elif self.itemsize == 4:
            casttype = ctypes.c_uint
        return ctypes.cast(src, ctypes.POINTER(casttype)).contents.value

    def _setitem(self, start, end, value):
        target = None
        if self.itemsize == 1:
            target = ctypes.cast(self.source, ctypes.POINTER(ctypes.c_ubyte))
        elif self.itemsize == 2:
            target = ctypes.cast(self.source, ctypes.POINTER(ctypes.c_ushort))
        elif self.itemsize == 3:
            # TODO
            raise NotImplementedError("unsupported bpp")
        elif self.itemsize == 4:
            target = ctypes.cast(self.source, ctypes.POINTER(ctypes.c_uint))
        value = prepare_color(value, self._surface)
        target[start // self.itemsize] = value

    def __del__(self):
        if self._surface is not None:
            if SDL_MUSTLOCK(self._surface):
                SDL_UnlockSurface(self._surface)

_HASNUMPY = True
try:
    import numpy

    class SurfaceArray(numpy.ndarray):
        """Wrapper class around numpy.ndarray.

        Used to keep track of the original source object for pixels2d()
        and pixels3d() to avoid the deletion of the source object.
        """
        def __new__(cls, shape, dtype=float, buffer_=None, offset=0,
                    strides=None, order=None, source=None, surface=None):
            sfarray = numpy.ndarray.__new__(cls, shape, dtype, buffer_,
                                            offset, strides, order)
            sfarray._source = source
            sfarray._surface = surface
            return sfarray

        def __array_finalize__(self, sfarray):
            if sfarray is None:
                return
            self._source = getattr(sfarray, '_source', None)
            self._surface = getattr(sfarray, '_surface', None)

        def __del__(self):
            if self._surface:
                if SDL_MUSTLOCK(self._surface):
                    SDL_UnlockSurface(self._surface)

except ImportError:
    _HASNUMPY = False


@experimental
def pixels2d(source):
    """Creates a 2D pixel array from the passed source."""
    if not _HASNUMPY:
        raise UnsupportedError(pixels2d, "numpy module could not be loaded")
    if isinstance(source, SoftwareSprite):
        psurface = source.surface
    elif isinstance(source, SDL_Surface):
        psurface = source
    else:
        raise TypeError("source must be a Sprite or SDL_Surface")

    bpp = psurface.format.contents.BytesPerPixel
    if bpp < 1 or bpp > 4:
        raise ValueError("unsupported bpp")
    strides = (psurface.pitch, bpp)
    srcsize = psurface.h * psurface.pitch
    shape = psurface.h, psurface.w   # surface.pitch // bpp

    dtypes = {1: numpy.uint8,
              2: numpy.uint16,
              3: numpy.uint32,
              4: numpy.uint32
              }

    if SDL_MUSTLOCK(psurface):
        SDL_LockSurface(psurface)
    pxbuf = ctypes.cast(psurface.pixels,
                        ctypes.POINTER(ctypes.c_ubyte * srcsize)).contents
    return SurfaceArray(shape, dtypes[bpp], pxbuf, 0, strides, "C", source,
                        psurface).transpose()


@experimental
def pixels3d(source):
    """Creates a 3D pixel array from the passed source.
    """
    if not _HASNUMPY:
        raise UnsupportedError(pixels3d, "numpy module could not be loaded")
    if isinstance(source, SoftwareSprite):
        psurface = source.surface
    elif isinstance(source, SDL_Surface):
        psurface = source
    else:
        raise TypeError("source must be a Sprite or SDL_Surface")

    bpp = psurface.format.contents.BytesPerPixel
    if bpp < 1 or bpp > 4:
        raise ValueError("unsupported bpp")
    strides = (psurface.pitch, bpp, 1)
    srcsize = psurface.h * psurface.pitch
    shape = psurface.h, psurface.w, bpp

    if SDL_MUSTLOCK(psurface):
        SDL_LockSurface(psurface)
    pxbuf = ctypes.cast(psurface.pixels,
                        ctypes.POINTER(ctypes.c_ubyte * srcsize)).contents
    return SurfaceArray(shape, numpy.uint8, pxbuf, 0, strides, "C", source,
                        psurface).transpose(1, 0, 2)
