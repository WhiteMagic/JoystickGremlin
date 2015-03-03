"""
Conversion routines for sequences.
"""
import ctypes

__all__ = ["CTypesView", "to_ctypes", "to_list", "to_tuple", "create_array",
           "MemoryView"]


# Hack around an import error using relative import paths in Python 2.7
_ARRAY = __import__("array")


def to_tuple(dataseq):
    """Converts a ctypes array to a tuple."""
    return tuple(dataseq)


def to_list(dataseq):
    """Converts a ctypes array to a list."""
    return list(dataseq)


def to_ctypes(dataseq, dtype, mcount=0):
    """Converts an arbitrary sequence to a ctypes array of the specified
    type and returns the ctypes array and amount of items as two-value
    tuple.

    Raises a TypeError, if one or more elements in the passed sequence
    do not match the passed type.
    """
    if mcount > 0:
        count = mcount
    else:
        count = len(dataseq)
    if isinstance(dataseq, CTypesView):
        itemsize = ctypes.sizeof(dtype)
        if itemsize == 1:
            dataseq = dataseq.to_bytes()
        elif itemsize == 2:
            dataseq = dataseq.to_uint16()
        elif itemsize == 4:
            dataseq = dataseq.to_uint32()
        elif itemsize == 8:
            dataseq = dataseq.to_uint64()
        else:
            raise TypeError("unsupported data type for the passed CTypesView")
    valset = (count * dtype)(*dataseq)
    return valset, count


def create_array(obj, itemsize):
    """Creates an array.array based copy of the passed object.

    itemsize denotes the size in bytes for a single element within obj.
    """
    if itemsize == 1:
        return _ARRAY.array("B", obj)
    elif itemsize == 2:
        return _ARRAY.array("H", obj)
    elif itemsize == 4:
        return _ARRAY.array("I", obj)
    elif itemsize == 8:
        return _ARRAY.array("d", obj)
    else:
        raise TypeError("unsupported data type")


class CTypesView(object):
    """A proxy for byte-wise accessible data types to be used in ctypes
    bindings.
    """
    def __init__(self, obj, itemsize=1, docopy=False, objsize=None):
        """Creates a new CTypesView for the passed object.

        Unless docopy is True, the CTypesView tries to let ctypes
        bindings and other callers access the object's contents
        directly.

        For certain types, such as the bytearray, the object must not be
        reassigned after being encapsuled and used in ctypes bindings,
        if the contents are not copied.
        """
        self._obj = obj
        self._isshared = True
        self._view = None
        self._itemsize = itemsize
        self._create_view(itemsize, bool(docopy), objsize)

    def _create_view(self, itemsize, docopy, objsize):
        """Creates the view on the specified object."""
        self._isshared = not docopy
        bsize = 0
        if objsize is None:
            bsize = len(self._obj) * itemsize
        else:
            bsize = objsize * itemsize

        if docopy:
            self._obj = create_array(self._obj, itemsize)
        try:
            self._view = (ctypes.c_ubyte * bsize).from_buffer(self._obj)
        except AttributeError:
            # pypy ctypes arrays do not feature a from_buffer() method.
            self._isshared = False
            # in case we requested a copy earlier, we do not need to recreate
            # the array, since we have it already. In any other case, create
            # a byte array.
            if not docopy:
                # Try to determine the itemsize again for array
                # instances, just in case the user assumed it to work.
                if isinstance(self._obj, _ARRAY.array):
                    itemsize = self._obj.itemsize
                    bsize = len(self._obj) * itemsize
                self._obj = create_array(self._obj, itemsize)
            self._view = (ctypes.c_ubyte * bsize)(*bytearray(self._obj))

    def __repr__(self):
        dtype = type(self._obj).__name__
        bsize = self.bytesize
        return "CTypesView(type=%s, bytesize=%d, shared=%s)" % (dtype, bsize,
                                                                self.is_shared)

    def __len__(self):
        """Returns the length of the underlying object in bytes."""
        return self.bytesize

    def to_bytes(self):
        """Returns a byte representation of the underlying object."""
        castval = ctypes.POINTER(ctypes.c_ubyte * self.bytesize)
        return ctypes.cast(self.view, castval).contents

    def to_uint16(self):
        """Returns a 16-bit unsigned integer array of the object data."""
        castval = ctypes.POINTER(ctypes.c_ushort * (self.bytesize // 2))
        return ctypes.cast(self.view, castval).contents

    def to_uint32(self):
        """Returns a 32-bit unsigned integer array of the object data."""
        castval = ctypes.POINTER(ctypes.c_uint * (self.bytesize // 4))
        return ctypes.cast(self.view, castval).contents

    def to_uint64(self):
        """Returns a 64-bit unsigned integer array of the object data."""
        castval = ctypes.POINTER(ctypes.c_ulonglong * (self.bytesize // 8))
        return ctypes.cast(self.view, castval).contents

    @property
    def bytesize(self):
        """The size in bytes of the underlying object."""
        return ctypes.sizeof(self.view)

    @property
    def view(self):
        """The ctypes view of the object."""
        return self._view

    @property
    def is_shared(self):
        """Indicates, if changes on the CTypesView data effect the
        underlying object directly.
        """
        return self._isshared

    @property
    def object(self):
        """The underlying object."""
        return self._obj


class MemoryView(object):
    """Simple n-dimensional access to buffers.

    The MemoryView provides a read-write access to arbitrary data
    objects, which can be indexed.

    NOTE: The MemoryView is a pure Python-based implementation and makes
    heavy use of recursion for multi-dimensional access. If you aim for
    speed on accessing a n-dimensional object, you want to consider
    using a specialised library such as numpy. If you need n-dimensional
    access support, where such a library is not supported, or if you
    need to provide access to objects, which do not fulfill the
    requirements of that particular libray, MemoryView can act as solid
    fallback solution.
    """
    def __init__(self, source, itemsize, strides, getfunc=None, setfunc=None,
                 srcsize=None):
        """Creates a new MemoryView from a source.

        itemsize denotes the size of a single item. strides defines the
        dimensions and the length (n items * itemsize) for each
        dimension. getfunc and setfunc are optional parameters to provide
        specialised read and write access to the underlying
        source. srcsize can be used to provide the correct source size,
        if len(source) does not return the absolute size of the source
        object in all dimensions.
        """
        self._source = source
        self._itemsize = itemsize
        self._strides = strides
        self._srcsize = srcsize or len(source)
        self._offset = 0

        self._getfunc = getfunc or self._getbytes
        self._setfunc = setfunc or self._setbytes

        tsum = 1
        for v in strides:
            tsum *= v
        if tsum > self._srcsize:
            raise ValueError("strides exceed the accesible source size")
        #if itemsize > strides[-1]:
        #    raise ValueError("itemsize exceeds the accessible stride length")

    def _getbytes(self, start, end):
        """Gets the bytes within the range of start:end."""
        return self._source[start:end]

    def _setbytes(self, start, end, value):
        """Gets the bytes within the range of start:end to the passed
        value.
        """
        self._source[start:end] = value

    def __len__(self):
        """The length of the MemoryView over the current dimension
        (amount of items for the current dimension).
        """
        return self.strides[0]

    def __repr__(self):
        retval = "["
        slen = self.strides[0]
        for dim in range(slen - 1):
            retval += "%s, " % self[dim]
        retval += str(self[slen - 1])
        retval += "]"
        return retval

    def __getitem__(self, index):
        """Returns the item at the specified index."""
        if type(index) is slice:
            raise IndexError("slicing is not supported")
        else:
            if index >= len(self):
                raise IndexError("index '%d'is out of bounds for '%d'" %
                                 (index, len(self)))
            if self.ndim == 1:
                offset = self._offset + index * self.itemsize
                return self._getfunc(offset, offset + self.itemsize)
            else:
                advance = self.itemsize
                for b in self.strides[1:]:
                    advance *= b
                offset = self._offset + advance * index
                view = MemoryView(self._source, self.itemsize,
                                  self.strides[1:], self._getfunc,
                                  self._setfunc, self._srcsize)
                view._offset = offset
                return view

    def __setitem__(self, index, value):
        """Sets the item at index to the specified value."""
        if type(index) is slice:
            raise IndexError("slicing is not supported")
        else:
            if index >= len(self):
                raise IndexError("index '%d'is out of bounds for '%d'" %
                                 (index, len(self)))
            offset = self._offset + index * self.itemsize
            if self.ndim == 1:
                self._setfunc(offset, offset + self.itemsize, value)
            else:
                advance = self.itemsize
                for b in self.strides[1:]:
                    advance *= b
                offset = self._offset + advance * index
                view = MemoryView(self._source, self.itemsize,
                                  self.strides[1:], self._getfunc,
                                  self._setfunc, self._srcsize)
                view._offset = offset
                if len(value) != len(view):
                    raise ValueError("value does not match the view strides")
                for x in range(len(view)):
                    view[x] = value[x]

    @property
    def size(self):
        """The size in bytes of the underlying source object."""
        return self._srcsize

    @property
    def strides(self):
        """A tuple defining the length in bytes for accessing all
        elements in each dimension of the MemoryView.
        """
        return self._strides

    @property
    def itemsize(self):
        """The size of a single item in bytes."""
        return self._itemsize

    @property
    def ndim(self):
        """The number of dimensions of the MemoryView."""
        return len(self.strides)

    @property
    def source(self):
        """The underlying data source."""
        return self._source
