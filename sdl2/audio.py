from ctypes import Structure, c_int, c_char_p, c_double, c_void_p, CFUNCTYPE, \
    POINTER
from .dll import _bind, nullfunc
from .endian import SDL_BYTEORDER, SDL_LIL_ENDIAN
from .stdinc import Uint8, Uint16, Uint32
from .rwops import SDL_RWops, SDL_RWFromFile

__all__ = ["SDL_AudioFormat", "SDL_AUDIO_MASK_BITSIZE",
           "SDL_AUDIO_MASK_DATATYPE", "SDL_AUDIO_MASK_ENDIAN",
           "SDL_AUDIO_MASK_SIGNED", "SDL_AUDIO_BITSIZE", "SDL_AUDIO_ISFLOAT",
           "SDL_AUDIO_ISBIGENDIAN", "SDL_AUDIO_ISSIGNED", "SDL_AUDIO_ISINT",
           "SDL_AUDIO_ISLITTLEENDIAN", "SDL_AUDIO_ISUNSIGNED", "AUDIO_U8",
           "AUDIO_S8", "AUDIO_U16LSB", "AUDIO_S16LSB", "AUDIO_U16MSB",
           "AUDIO_S16MSB", "AUDIO_U16", "AUDIO_S16", "AUDIO_S32LSB",
           "AUDIO_S32MSB", "AUDIO_S32", "AUDIO_F32LSB", "AUDIO_S32MSB",
           "AUDIO_F32", "AUDIO_U16SYS", "AUDIO_S16SYS", "AUDIO_S32SYS", "AUDIO_FORMATS",
           "AUDIO_F32SYS", "SDL_AUDIO_ALLOW_FREQUENCY_CHANGE",
           "SDL_AUDIO_ALLOW_FORMAT_CHANGE", "SDL_AUDIO_ALLOW_CHANNELS_CHANGE",
           "SDL_AUDIO_ALLOW_ANY_CHANGE", "SDL_AudioCallback", "SDL_AudioSpec",
           "SDL_AudioCVT", "SDL_AudioFilter", "SDL_GetNumAudioDrivers",
           "SDL_GetAudioDriver", "SDL_AudioInit", "SDL_AudioQuit",
           "SDL_GetCurrentAudioDriver", "SDL_OpenAudio", "SDL_AudioDeviceID",
           "SDL_GetNumAudioDevices", "SDL_GetAudioDeviceName",
           "SDL_OpenAudioDevice", "SDL_AUDIO_STOPPED", "SDL_AUDIO_PLAYING",
           "SDL_AUDIO_PAUSED", "SDL_AudioStatus", "SDL_GetAudioStatus",
           "SDL_GetAudioDeviceStatus", "SDL_PauseAudio", "SDL_PauseAudioDevice",
           "SDL_LoadWAV_RW", "SDL_LoadWAV", "SDL_FreeWAV", "SDL_BuildAudioCVT",
           "SDL_ConvertAudio", "SDL_MIX_MAXVOLUME", "SDL_MixAudio",
           "SDL_MixAudioFormat", "SDL_LockAudio", "SDL_LockAudioDevice",
           "SDL_UnlockAudio", "SDL_UnlockAudioDevice", "SDL_CloseAudio",
           "SDL_CloseAudioDevice", "SDL_QueueAudio", "SDL_GetQueuedAudioSize",
           "SDL_ClearQueuedAudio", "SDL_DequeueAudio"
         ]

SDL_AudioFormat = Uint16

SDL_AUDIO_MASK_BITSIZE = 0xFF
SDL_AUDIO_MASK_DATATYPE = 1 << 8
SDL_AUDIO_MASK_ENDIAN = 1 << 12
SDL_AUDIO_MASK_SIGNED = 1 << 15
SDL_AUDIO_BITSIZE = lambda x: (x & SDL_AUDIO_MASK_BITSIZE)
SDL_AUDIO_ISFLOAT = lambda x: (x & SDL_AUDIO_MASK_DATATYPE)
SDL_AUDIO_ISBIGENDIAN = lambda x: (x & SDL_AUDIO_MASK_ENDIAN)
SDL_AUDIO_ISSIGNED = lambda x: (x & SDL_AUDIO_MASK_SIGNED)
SDL_AUDIO_ISINT = lambda x: (not SDL_AUDIO_ISFLOAT(x))
SDL_AUDIO_ISLITTLEENDIAN = lambda x: (not SDL_AUDIO_ISBIGENDIAN(x))
SDL_AUDIO_ISUNSIGNED = lambda x: (not SDL_AUDIO_ISSIGNED(x))

AUDIO_U8 = 0x0008
AUDIO_S8 = 0x8008
AUDIO_U16LSB = 0x0010
AUDIO_S16LSB = 0x8010
AUDIO_U16MSB = 0x1010
AUDIO_S16MSB = 0x9010
AUDIO_U16 = AUDIO_U16LSB
AUDIO_S16 = AUDIO_S16LSB
AUDIO_S32LSB = 0x8020
AUDIO_S32MSB = 0x9020
AUDIO_S32 = AUDIO_S32LSB
AUDIO_F32LSB = 0x8120
AUDIO_F32MSB = 0x9120
AUDIO_F32 = AUDIO_F32LSB


# All of the audio formats should be in this set which is provided as a
# convenience to the end user for purposes of iteration and validation.
# (is the provided audio format in the supported set?)
AUDIO_FORMATS = set([AUDIO_U8, AUDIO_S8, AUDIO_U16LSB, AUDIO_S16LSB,
                     AUDIO_U16MSB, AUDIO_S16MSB, AUDIO_U16, AUDIO_S16,
                     AUDIO_S32LSB, AUDIO_S32MSB, AUDIO_S32, AUDIO_F32LSB,
                     AUDIO_F32MSB, AUDIO_F32])

if SDL_BYTEORDER == SDL_LIL_ENDIAN:
    AUDIO_U16SYS = AUDIO_U16LSB
    AUDIO_S16SYS = AUDIO_S16LSB
    AUDIO_S32SYS = AUDIO_S32LSB
    AUDIO_F32SYS = AUDIO_F32LSB
else:
    AUDIO_U16SYS = AUDIO_U16MSB
    AUDIO_S16SYS = AUDIO_S16MSB
    AUDIO_S32SYS = AUDIO_S32MSB
    AUDIO_F32SYS = AUDIO_F32MSB

SDL_AUDIO_ALLOW_FREQUENCY_CHANGE = 0x00000001
SDL_AUDIO_ALLOW_FORMAT_CHANGE = 0x00000002
SDL_AUDIO_ALLOW_CHANNELS_CHANGE = 0x00000004
SDL_AUDIO_ALLOW_ANY_CHANGE = (SDL_AUDIO_ALLOW_FREQUENCY_CHANGE |
                              SDL_AUDIO_ALLOW_FORMAT_CHANGE |
                              SDL_AUDIO_ALLOW_CHANNELS_CHANGE)

SDL_AudioCallback = CFUNCTYPE(None, c_void_p, POINTER(Uint8), c_int)

class SDL_AudioSpec(Structure):
    _fields_ = [("freq", c_int),
                ("format", SDL_AudioFormat),
                ("channels", Uint8),
                ("silence", Uint8),
                ("samples", Uint16),
                ("padding", Uint16),
                ("size", Uint32),
                ("callback", SDL_AudioCallback),
                ("userdata", c_void_p)
                ]
    def __init__(self, freq, aformat, channels, samples,
                 callback=SDL_AudioCallback(), userdata=c_void_p(0)):
        super(SDL_AudioSpec, self).__init__()
        self.freq = freq
        self.format = aformat
        self.channels = channels
        self.samples = samples
        self.callback = callback
        self.userdata = userdata

class SDL_AudioCVT(Structure):
    pass

SDL_AudioFilter = CFUNCTYPE(POINTER(SDL_AudioCVT), SDL_AudioFormat)
SDL_AudioCVT._fields_ = [("needed", c_int),
                         ("src_format", SDL_AudioFormat),
                         ("dst_format", SDL_AudioFormat),
                         ("rate_incr", c_double),
                         ("buf", POINTER(Uint8)),
                         ("len", c_int),
                         ("len_cvt", c_int),
                         ("len_mult", c_int),
                         ("len_ratio", c_double),
                         ("filters", (SDL_AudioFilter * 10)),
                         ("filter_index", c_int)
                         ]

SDL_GetNumAudioDrivers = _bind("SDL_GetNumAudioDrivers", None, c_int)
SDL_GetAudioDriver = _bind("SDL_GetAudioDriver", [c_int], c_char_p)
SDL_AudioInit = _bind("SDL_AudioInit", [c_char_p], c_int)
SDL_AudioQuit = _bind("SDL_AudioQuit")
SDL_GetCurrentAudioDriver = _bind("SDL_GetCurrentAudioDriver", None, c_char_p)
SDL_OpenAudio = _bind("SDL_OpenAudio", [POINTER(SDL_AudioSpec), POINTER(SDL_AudioSpec)], c_int)
SDL_AudioDeviceID = Uint32
SDL_GetNumAudioDevices = _bind("SDL_GetNumAudioDevices", [c_int], c_int)
SDL_GetAudioDeviceName = _bind("SDL_GetAudioDeviceName", [c_int, c_int], c_char_p)
SDL_OpenAudioDevice = _bind("SDL_OpenAudioDevice", [c_char_p, c_int, POINTER(SDL_AudioSpec), POINTER(SDL_AudioSpec), c_int], SDL_AudioDeviceID)
SDL_AUDIO_STOPPED = 0
SDL_AUDIO_PLAYING = 1
SDL_AUDIO_PAUSED = 2
SDL_AudioStatus = c_int
SDL_GetAudioStatus = _bind("SDL_GetAudioStatus", None, SDL_AudioStatus)
SDL_GetAudioDeviceStatus = _bind("SDL_GetAudioDeviceStatus", [SDL_AudioDeviceID], SDL_AudioStatus)
SDL_PauseAudio = _bind("SDL_PauseAudio", [c_int])
SDL_PauseAudioDevice = _bind("SDL_PauseAudioDevice", [SDL_AudioDeviceID, c_int])
SDL_LoadWAV_RW = _bind("SDL_LoadWAV_RW", [POINTER(SDL_RWops), c_int, POINTER(SDL_AudioSpec), POINTER(POINTER(Uint8)), POINTER(Uint32)], POINTER(SDL_AudioSpec))
SDL_LoadWAV = lambda f, s, ab, al: SDL_LoadWAV_RW(SDL_RWFromFile(f, b"rb"), 1, s, ab , al)
SDL_FreeWAV = _bind("SDL_FreeWAV", [POINTER(Uint8)])
SDL_BuildAudioCVT = _bind("SDL_BuildAudioCVT", [POINTER(SDL_AudioCVT), SDL_AudioFormat, Uint8, c_int, SDL_AudioFormat, Uint8, c_int], c_int)
SDL_ConvertAudio = _bind("SDL_ConvertAudio", [POINTER(SDL_AudioCVT)], c_int)
SDL_MIX_MAXVOLUME = 128
SDL_MixAudio = _bind("SDL_MixAudio", [POINTER(Uint8), POINTER(Uint8), Uint32, c_int])
SDL_MixAudioFormat = _bind("SDL_MixAudioFormat", [POINTER(Uint8), POINTER(Uint8), SDL_AudioFormat, Uint32, c_int])
SDL_LockAudio = _bind("SDL_LockAudio")
SDL_LockAudioDevice = _bind("SDL_LockAudioDevice", [SDL_AudioDeviceID])
SDL_UnlockAudio = _bind("SDL_UnlockAudio")
SDL_UnlockAudioDevice = _bind("SDL_UnlockAudioDevice", [SDL_AudioDeviceID])
SDL_CloseAudio = _bind("SDL_CloseAudio")
SDL_CloseAudioDevice = _bind("SDL_CloseAudioDevice", [SDL_AudioDeviceID])
SDL_QueueAudio = _bind("SDL_QueueAudio", [SDL_AudioDeviceID, c_void_p, Uint32], c_int, nullfunc)
SDL_DequeueAudio = _bind("SDL_DequeueAudio", [SDL_AudioDeviceID, c_void_p, Uint32], Uint32, nullfunc)
SDL_GetQueuedAudioSize = _bind("SDL_GetQueuedAudioSize", [SDL_AudioDeviceID], Uint32, nullfunc)
SDL_ClearQueuedAudio = _bind("SDL_ClearQueuedAudio", [SDL_AudioDeviceID], optfunc=nullfunc)

