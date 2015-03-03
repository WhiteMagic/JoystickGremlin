from ctypes import Structure, c_int, POINTER
from .dll import _bind
from .stdinc import SDL_bool

__all__ = ["SDL_Point", "SDL_Rect", "SDL_RectEmpty", "SDL_RectEquals",
           "SDL_HasIntersection", "SDL_IntersectRect", "SDL_UnionRect",
           "SDL_EnclosePoints", "SDL_IntersectRectAndLine",
           "SDL_PointInRect"
           ]


class SDL_Point(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

    def __init__(self, x=0, y=0):
        super(SDL_Point, self).__init__()
        self.x = x
        self.y = y

    def __repr__(self):
        return "SDL_Point(x=%d, y=%d)" % (self.x, self.y)

    def __copy__(self):
        return SDL_Point(self.x, self.y)

    def __deepcopy__(self, memo):
        return SDL_Point(self.x, self.y)

    def __eq__(self, pt):
        return self.x == pt.x and self.y == pt.y

    def __ne__(self, pt):
        return self.x != pt.x or self.y != pt.y


class SDL_Rect(Structure):
    _fields_ = [("x", c_int), ("y", c_int),
                ("w", c_int), ("h", c_int)]

    def __init__(self, x=0, y=0, w=0, h=0):
        super(SDL_Rect, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __repr__(self):
        return "SDL_Rect(x=%d, y=%d, w=%d, h=%d)" % (self.x, self.y, self.w,
                                                     self.h)

    def __copy__(self):
        return SDL_Rect(self.x, self.y, self.w, self.h)

    def __deepcopy__(self, memo):
        return SDL_Rect(self.x, self.y, self.w, self.h)

    def __eq__(self, rt):
        return self.x == rt.x and self.y == rt.y and \
            self.w == rt.w and self.h == rt.h

    def __ne__(self, rt):
        return self.x != rt.x or self.y != rt.y or \
            self.w != rt.w or self.h != rt.h


SDL_RectEmpty = lambda x: ((not x) or (x.w <= 0) or (x.h <= 0))
SDL_RectEquals = lambda a, b: ((a.x == b.x) and (a.y == b.y) and
                               (a.w == b.w) and (a.h == b.h))
SDL_PointInRect = lambda p, r: ((p.x >= r.x) and (p.x < (r.x + r.w)) and
                                (p.y >= r.y) and (p.y < (r.y + r.h)))
SDL_HasIntersection = _bind("SDL_HasIntersection", [POINTER(SDL_Rect), POINTER(SDL_Rect)], SDL_bool)
SDL_IntersectRect = _bind("SDL_IntersectRect", [POINTER(SDL_Rect), POINTER(SDL_Rect), POINTER(SDL_Rect)], SDL_bool)
SDL_UnionRect = _bind("SDL_UnionRect", [POINTER(SDL_Rect), POINTER(SDL_Rect), POINTER(SDL_Rect)])
SDL_EnclosePoints = _bind("SDL_EnclosePoints", [POINTER(SDL_Point), c_int, POINTER(SDL_Rect), POINTER(SDL_Rect)], SDL_bool)
SDL_IntersectRectAndLine = _bind("SDL_IntersectRectAndLine", [POINTER(SDL_Rect), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)], SDL_bool)
