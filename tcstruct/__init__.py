""" C-type structures for Python using type annotations """
import sys
from typing import SupportsIndex, Literal, Self, Sequence, Callable, Any, Tuple
import struct
import ctypes
from ctypes._endian import _other_endian

Array = Sequence
BitField = Tuple


class tcstruct_type:
    _byteorder: Literal["little", "big"] | None = None
    _char: Literal["x", "c", "b", "B", "?", "h", "H", "i", "I", "l", "L", "q", "Q", "n", "N", "e", "f", "d", "s", "p", "P"] = None

    def __init__(self, *args, **kwargs):
        pass

    def pack(self, byteorder: Literal["little", "big"] | None = None) -> bytes:
        if byteorder is None:
            byteorder = self._byteorder
        format = {None: "", "little": "<", "big": ">"}[byteorder]
        return struct.pack(f"{format}{self._char}", self)

    @classmethod
    def with_byteorder(cls, value, byteorder: Literal["little", "big"]) -> Self:
        self = cls(value)
        self._byteorder = byteorder
        return self

    def __class_getitem__(cls, item):
        return type(f'{cls.__name__}[{item}]', (cls, ), {"_array": item})


class tcstruct_int(int, tcstruct_type):
    _signed: bool = None
    _bitwidth: int = None
    _byteorder: Literal["little", "big"] = "big"
    _char: Literal["x", "c", "b", "B", "?", "h", "H", "i", "I", "l", "L", "q", "Q", "n", "N", "e", "f", "d", "s", "p", "P"] = None

    def to_bytes(self,
                 length: SupportsIndex | None = None,
                 byteorder: Literal["little", "big"] | None = None,
                 *,
                 signed: bool | None = None) -> bytes:
        """Return an array of bytes representing an integer. See int.to_bytes() for details."""
        if length is None:
            length: SupportsIndex = self._bitwidth // 8
        if byteorder is None:
            byteorder = self._byteorder
        if signed is None:
            signed = self._signed

        return int.to_bytes(self, length, byteorder, signed=signed)

    def __bytes__(self):
        return self.to_bytes()


class tcstruct_uint(tcstruct_int):
    _signed = False


class uint8_t(tcstruct_uint):
    _bitwidth = 8
    _char = "B"
    _ctype = ctypes.c_uint8


class uint16_t(tcstruct_uint):
    _bitwidth = 16
    _char = "H"
    _ctype = ctypes.c_uint16


class uint32_t(tcstruct_uint):
    _bitwidth = 32
    _char = "I"
    _ctype = ctypes.c_uint32


class uint64_t(tcstruct_uint):
    _bitwidth = 64
    _char = "Q"
    _ctype = ctypes.c_uint64


class tcstruct_sint(tcstruct_int):
    _signed = True


class sint8_t(tcstruct_sint):
    _bitwidth = 8
    _char = "b"
    _ctype = ctypes.c_int8


class sint16_t(tcstruct_sint):
    _bitwidth = 16
    _char = "h"
    _ctype = ctypes.c_int16


class sint32_t(tcstruct_sint):
    _bitwidth = 32
    _char = "i"
    _ctype = ctypes.c_int32


class sint64_t(tcstruct_sint):
    _bitwidth = 64
    _char = "q"
    _ctype = ctypes.c_int64


int8_t = sint8_t
int16_t = sint16_t
int32_t = sint32_t
int64_t = sint64_t


class tcstruct_float(float, tcstruct_type):
    _signed: bool = True
    _bitwidth: int = None
    _char: Literal["f", "d"] = None


class float32_t(tcstruct_float):
    _bitwidth = 32
    _char = "f"
    _ctype = ctypes.c_float


class float64_t(tcstruct_float):
    _bitwidth = 64
    _char = "d"
    _ctype = ctypes.c_double


float_t = float32_t
double_t = float64_t


def gettype(x: Any, swap: bool) -> type:
    if swap:
        return _other_endian(_gettype(x))
    else:
        return _gettype(x)


def _gettype(x: Any) -> type:
    try:
        x = x.__args__[0]
    except AttributeError:
        pass
    try:
        try:
            return x._ctype * x._array
        except AttributeError:
            return x._ctype
    except AttributeError:
        return x


class TCStructMeta(type(ctypes.Structure)):
    """Metaclass of TCStruct"""

    def __new__(cls, name, bases, attrs):
        print(f'new({name=}, {bases=}, {attrs=})')
        if '__annotations__' in attrs:

            fields_base = []
            try:
                if '_fields_' not in attrs:
                    fields_base = next(list(b._fields_)
                                       for base in bases
                                       for b in base.__mro__
                                       if issubclass(b, ctypes.Structure) and hasattr(b, '_fields_'))
            except StopIteration:
                pass

            byteorder = attrs.get('_byteorder', None)
            try:
                if '_byteorder' not in attrs:
                    byteorder = next(b._byteorder
                                     for base in bases
                                     for b in base.__mro__
                                     if issubclass(b, TCStruct) and hasattr(b, '_byteorder'))
            except StopIteration:
                pass

            swap = byteorder is not None and sys.byteorder != byteorder

            fields = attrs.setdefault('_fields_', fields_base)
            fields.extend([(aname, gettype(atype, swap))
                           for aname, atype in attrs['__annotations__'].items()
                           if not aname.startswith('_')])


        return super().__new__(cls, name, bases, attrs)


class TCStruct(ctypes.Structure, metaclass=TCStructMeta):
    _byteorder = None
    __bytes__: Callable[[], bytes]

    def __init__(self, *args, **kwargs) -> None:
        kwargs_new = dict(zip((name for name, *_ in self._fields_), args))
        overlap = kwargs.keys() & kwargs_new.keys()
        if overlap:
            raise TypeError(f"{self.__class__.__name__}() got multiple values for argument '{overlap.pop()}'")
        kwargs_new.update(kwargs)
        super().__init__(**kwargs_new)

    @classmethod
    def from_bytes(cls, data, byteorder=None):
        return cls.from_buffer_copy(data)

    def to_bytes(self, byteorder=None):
        return bytes(self)


class LittleEndianStruct(TCStruct):
    _byteorder = 'little'
    if sys.byteorder != _byteorder:
        _swappedbytes_ = None


class BigEndianStruct(TCStruct):
    _byteorder = 'big'
    if sys.byteorder != _byteorder:
        _swappedbytes_ = None


Struct = LittleEndianStruct if sys.byteorder == 'little' else BigEndianStruct

__all__ = (Struct, BigEndianStruct, LittleEndianStruct,
           Array, BitField,
           uint8_t, uint16_t, uint32_t, uint64_t,
           sint8_t, sint16_t, sint32_t, sint64_t,
           int8_t, int16_t, int32_t, int64_t,
           float_t, double_t,
           float32_t, float64_t,
           )
