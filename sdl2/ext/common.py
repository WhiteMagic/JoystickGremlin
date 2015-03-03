"""SDL2 helper functions."""
import ctypes
from .. import SDL_Init, SDL_Quit, SDL_QuitSubSystem, SDL_WasInit, \
    SDL_INIT_VIDEO, error, events, timer

_HASSDLTTF = True
try:
    from .. import sdlttf
except ImportError:
    _HASSDLTTF = False
_HASSDLIMAGE = True
try:
    from .. import sdlimage
except ImportError:
    _HASSDLIMAGE = False

__all__ = ["SDLError", "init", "quit", "get_events", "TestEventProcessor"]


class SDLError(Exception):
    """A SDL2 specific exception class."""
    def __init__(self, msg=None):
        """Creates a new SDLError instance with the specified message.

        If no msg is passed, it will try to get the current SDL2 error via
        sdl2.error.SDL_GetError().
        """
        super(SDLError, self).__init__()
        self.msg = msg
        if not msg:
            self.msg = error.SDL_GetError()

    def __str__(self):
        return repr(self.msg)


def init():
    """Initializes the SDL2 video subsystem.

    Raises a SDLError, if the SDL2 video subsystem could not be
    initialised.
    """
    if SDL_Init(SDL_INIT_VIDEO) != 0:
        raise SDLError()


def quit():
    """Quits the SDL2 video subysystem.

    If no other subsystems are active, this will also call
    sdl2.SDL_Quit(), sdlttf.TTF_Quit() and sdlimage.IMG_Quit().
    """
    SDL_QuitSubSystem(SDL_INIT_VIDEO)
    if SDL_WasInit(0) != 0:
        if _HASSDLTTF and sdlttf.TTF_WasInit() == 1:
            sdlttf.TTF_Quit()
        if _HASSDLIMAGE:
            sdlimage.IMG_Quit()
        SDL_Quit()


def get_events():
    """Gets all SDL events that are currently on the event queue."""
    events.SDL_PumpEvents()

    evlist = []
    SDL_PeepEvents = events.SDL_PeepEvents

    op = events.SDL_GETEVENT
    first = events.SDL_FIRSTEVENT
    last = events.SDL_LASTEVENT

    while True:
        evarray = (events.SDL_Event * 10)()
        ptr = ctypes.cast(evarray, ctypes.POINTER(events.SDL_Event))
        ret = SDL_PeepEvents(ptr, 10, op, first, last)
        if ret <= 0:
            break
        evlist += list(evarray)[:ret]
        if ret < 10:
            break
    return evlist


class TestEventProcessor(object):
    """A simple event processor for testing purposes."""
    def run(self, window):
        """Starts an event loop without actually processing any event."""
        event = events.SDL_Event()
        running = True
        while running:
            ret = events.SDL_PollEvent(ctypes.byref(event), 1)
            if ret == 1:
                if event.type == events.SDL_QUIT:
                    running = False
                    break
            window.refresh()
            timer.SDL_Delay(10)
