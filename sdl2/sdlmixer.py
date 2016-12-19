import os
from ctypes import Structure, POINTER, CFUNCTYPE, c_int, c_char_p, c_void_p, \
    c_double
from .dll import DLL
from .version import SDL_version
from .audio import AUDIO_S16LSB, AUDIO_S16MSB
from .stdinc import Uint8, Uint16, Uint32, Sint16
from .endian import SDL_LIL_ENDIAN, SDL_BYTEORDER
from .rwops import SDL_RWops, SDL_RWFromFile
from .error import SDL_SetError, SDL_GetError

__all__ = ["get_dll_file", "SDL_MIXER_MAJOR_VERSION", "SDL_MIXER_MINOR_VERSION",
           "SDL_MIXER_PATCHLEVEL", "SDL_MIXER_VERSION", "MIX_MAJOR_VERSION",
           "MIX_MINOR_VERSION", "MIX_PATCHLEVEL", "MIX_VERSION",
           "Mix_Linked_Version", "MIX_InitFlags", "MIX_INIT_FLAC",
           "MIX_INIT_MOD", "MIX_INIT_MP3", "MIX_INIT_OGG",
           "MIX_INIT_FLUIDSYNTH", "Mix_Init", "Mix_Quit", "MIX_CHANNELS",
           "MIX_DEFAULT_FREQUENCY" , "MIX_DEFAULT_FORMAT",
           "MIX_DEFAULT_CHANNELS", "MIX_MAX_VOLUME", "Mix_Chunk", "Mix_Fading",
           "MIX_NO_FADING", "MIX_FADING_OUT", "MIX_FADING_IN", "Mix_MusicType",
           "MUS_NONE", "MUS_CMD", "MUS_WAV", "MUS_MOD", "MUS_MID", "MUS_OGG",
           "MUS_MP3", "MUS_MP3_MAD", "MUS_FLAC", "MUS_MODPLUG", "Mix_Music",
           "Mix_OpenAudio", "Mix_AllocateChannels", "Mix_QuerySpec",
           "Mix_LoadWAV_RW", "Mix_LoadWAV", "Mix_LoadMUS", "Mix_LoadMUS_RW",
           "Mix_LoadMUSType_RW", "Mix_QuickLoad_WAV", "Mix_QuickLoad_RAW",
           "Mix_FreeChunk", "Mix_FreeMusic", "Mix_GetNumChunkDecoders",
           "Mix_GetChunkDecoder", "Mix_GetNumMusicDecoders",
           "Mix_GetMusicDecoder", "Mix_GetMusicType", "mix_func",
           "Mix_SetPostMix", "Mix_HookMusic", "music_finished",
           "Mix_HookMusicFinished", "Mix_GetMusicHookData", "channel_finished",
           "Mix_ChannelFinished", "MIX_CHANNEL_POST", "Mix_EffectFunc_t",
           "Mix_EffectDone_t", "Mix_RegisterEffect", "Mix_UnregisterEffect",
           "Mix_UnregisterAllEffects", "MIX_EFFECTSMAXSPEED", "Mix_SetPanning",
           "Mix_SetPosition", "Mix_SetDistance", "Mix_SetReverseStereo",
           "Mix_ReserveChannels", "Mix_GroupChannel", "Mix_GroupChannels",
           "Mix_GroupAvailable", "Mix_GroupCount", "Mix_GroupOldest",
           "Mix_GroupNewer", "Mix_PlayChannel", "Mix_PlayChannelTimed",
           "Mix_PlayMusic", "Mix_FadeInMusic", "Mix_FadeInMusicPos",
           "Mix_FadeInChannel", "Mix_FadeInChannelTimed", "Mix_Volume",
           "Mix_VolumeChunk", "Mix_VolumeMusic", "Mix_HaltChannel",
           "Mix_HaltGroup", "Mix_HaltMusic", "Mix_ExpireChannel",
           "Mix_FadeOutChannel", "Mix_FadeOutGroup", "Mix_FadeOutMusic",
           "Mix_FadingMusic", "Mix_FadingChannel", "Mix_Pause", "Mix_Resume",
           "Mix_Paused", "Mix_PauseMusic", "Mix_ResumeMusic", "Mix_RewindMusic",
           "Mix_PausedMusic", "Mix_SetMusicPosition", "Mix_Playing",
           "Mix_PlayingMusic", "Mix_SetMusicCMD", "Mix_SetSynchroValue",
           "Mix_GetSynchroValue", "Mix_SetSoundFonts", "Mix_GetSoundFonts",
           "soundfont_function", "Mix_EachSoundFont", "Mix_GetChunk",
           "Mix_CloseAudio", "Mix_SetError", "Mix_GetError"
          ]

try:
    dll = DLL("SDL2_mixer", ["SDL2_mixer", "SDL2_mixer-2.0"],
              os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)


def get_dll_file():
    """Gets the file name of the loaded SDL2_mixer library."""
    return dll.libfile

_bind = dll.bind_function

SDL_MIXER_MAJOR_VERSION = 2
SDL_MIXER_MINOR_VERSION = 0
SDL_MIXER_PATCHLEVEL = 0


def SDL_MIXER_VERSION(x):
    x.major = SDL_MIXER_MAJOR_VERSION
    x.minor = SDL_MIXER_MINOR_VERSION
    x.patch = SDL_MIXER_PATCHLEVEL

MIX_MAJOR_VERSION = SDL_MIXER_MAJOR_VERSION
MIX_MINOR_VERSION = SDL_MIXER_MINOR_VERSION
MIX_PATCHLEVEL = SDL_MIXER_PATCHLEVEL
MIX_VERSION = SDL_MIXER_VERSION

Mix_Linked_Version = _bind("Mix_Linked_Version", None, POINTER(SDL_version))
MIX_InitFlags = c_int
MIX_INIT_FLAC = 0x00000001
MIX_INIT_MOD =  0x00000002
MIX_INIT_MODPLUG = 0x00000004
MIX_INIT_MP3 = 0x00000008
MIX_INIT_OGG = 0x000000010
MIX_INIT_FLUIDSYNTH = 0x00000020

Mix_Init = _bind("Mix_Init", [c_int], c_int)
Mix_Quit = _bind("Mix_Quit")

MIX_CHANNELS = 8
MIX_DEFAULT_FREQUENCY = 22050
if SDL_BYTEORDER == SDL_LIL_ENDIAN:
    MIX_DEFAULT_FORMAT = AUDIO_S16LSB
else:
    MIX_DEFAULT_FORMAT = AUDIO_S16MSB
MIX_DEFAULT_CHANNELS = 2
MIX_MAX_VOLUME = 128

class Mix_Chunk(Structure):
    _fields_ = [("allocated", c_int),
                ("abuf", POINTER(Uint8)),
                ("alen", Uint32),
                ("volume", Uint8)]

Mix_Fading = c_int
MIX_NO_FADING = 0
MIX_FADING_OUT = 1
MIX_FADING_IN = 2
Mix_MusicType = c_int
MUS_NONE = 0
MUS_CMD = 1
MUS_WAV = 2
MUS_MOD = 3
MUS_MID = 4
MUS_OGG = 5
MUS_MP3 = 6
MUS_MP3_MAD = 7
MUS_FLAC = 8
MUS_MODPLUG = 9

class Mix_Music(Structure):
    pass

Mix_OpenAudio = _bind("Mix_OpenAudio", [c_int, Uint16, c_int, c_int], c_int)
Mix_AllocateChannels = _bind("Mix_AllocateChannels", [c_int], c_int)
Mix_QuerySpec = _bind("Mix_QuerySpec", [POINTER(c_int), POINTER(Uint16), POINTER(c_int)], c_int)
Mix_LoadWAV_RW = _bind("Mix_LoadWAV_RW", [POINTER(SDL_RWops), c_int], POINTER(Mix_Chunk))
Mix_LoadWAV = lambda fname: Mix_LoadWAV_RW(SDL_RWFromFile(fname, b"rb"), 1)
Mix_LoadMUS = _bind("Mix_LoadMUS", [c_char_p], POINTER(Mix_Music))
Mix_LoadMUS_RW = _bind("Mix_LoadMUS_RW", [POINTER(SDL_RWops)], POINTER(Mix_Music))
Mix_LoadMUSType_RW = _bind("Mix_LoadMUSType_RW", [POINTER(SDL_RWops), Mix_MusicType, c_int], POINTER(Mix_Music))
Mix_QuickLoad_WAV = _bind("Mix_QuickLoad_WAV", [POINTER(Uint8)], POINTER(Mix_Chunk))
Mix_QuickLoad_RAW = _bind("Mix_QuickLoad_RAW", [POINTER(Uint8), Uint32], POINTER(Mix_Chunk))
Mix_FreeChunk = _bind("Mix_FreeChunk", [POINTER(Mix_Chunk)])
Mix_FreeMusic = _bind("Mix_FreeMusic", [POINTER(Mix_Music)])
Mix_GetNumChunkDecoders = _bind("Mix_GetNumChunkDecoders", None, c_int)
Mix_GetChunkDecoder = _bind("Mix_GetChunkDecoder", [c_int], c_char_p)
Mix_GetNumMusicDecoders = _bind("Mix_GetNumMusicDecoders", None, c_int)
Mix_GetMusicDecoder = _bind("Mix_GetMusicDecoder", [c_int], c_char_p)
Mix_GetMusicType = _bind("Mix_GetMusicType", [POINTER(Mix_Music)], Mix_MusicType)
mix_func = CFUNCTYPE(None, c_void_p, POINTER(Uint8), c_int)
Mix_SetPostMix = _bind("Mix_SetPostMix", [mix_func, c_void_p])
Mix_HookMusic = _bind("Mix_HookMusic", [mix_func, c_void_p])
music_finished = CFUNCTYPE(None)
Mix_HookMusicFinished = _bind("Mix_HookMusicFinished", [music_finished])
Mix_GetMusicHookData = _bind("Mix_GetMusicHookData", None, c_void_p)
channel_finished = CFUNCTYPE(None, c_int)
Mix_ChannelFinished = _bind("Mix_ChannelFinished", [channel_finished])
MIX_CHANNEL_POST = -2
Mix_EffectFunc_t = CFUNCTYPE(None, c_int, c_void_p, c_int, c_void_p)
Mix_EffectDone_t = CFUNCTYPE(None, c_int, c_void_p)
Mix_RegisterEffect = _bind("Mix_RegisterEffect", [c_int, Mix_EffectFunc_t, Mix_EffectDone_t, c_void_p], c_int)
Mix_UnregisterEffect = _bind("Mix_UnregisterEffect", [c_int, Mix_EffectFunc_t], c_int)
Mix_UnregisterAllEffects = _bind("Mix_UnregisterAllEffects", [c_int])
MIX_EFFECTSMAXSPEED = "MIX_EFFECTSMAXSPEED"
Mix_SetPanning = _bind("Mix_SetPanning", [c_int, Uint8, Uint8], c_int)
Mix_SetPosition = _bind("Mix_SetPosition", [c_int, Sint16, Uint8], c_int)
Mix_SetDistance = _bind("Mix_SetDistance", [c_int, Uint8])
Mix_SetReverseStereo = _bind("Mix_SetReverseStereo", [c_int, c_int], c_int)
Mix_ReserveChannels = _bind("Mix_ReserveChannels", [c_int], c_int)
Mix_GroupChannel = _bind("Mix_GroupChannel", [c_int, c_int], c_int)
Mix_GroupChannels = _bind("Mix_GroupChannels", [c_int, c_int, c_int], c_int)
Mix_GroupAvailable = _bind("Mix_GroupAvailable", [c_int], c_int)
Mix_GroupCount = _bind("Mix_GroupCount", [c_int], c_int)
Mix_GroupOldest = _bind("Mix_GroupOldest", [c_int], c_int)
Mix_GroupNewer = _bind("Mix_GroupNewer", [c_int], c_int)
Mix_PlayChannel = lambda channel, chunk, loops: Mix_PlayChannelTimed(channel, chunk, loops, -1)
Mix_PlayChannelTimed = _bind("Mix_PlayChannelTimed", [c_int, POINTER(Mix_Chunk), c_int, c_int], c_int)
Mix_PlayMusic = _bind("Mix_PlayMusic", [POINTER(Mix_Music), c_int], c_int)
Mix_FadeInMusic = _bind("Mix_FadeInMusic", [POINTER(Mix_Music), c_int, c_int], c_int)
Mix_FadeInMusicPos = _bind("Mix_FadeInMusicPos", [POINTER(Mix_Music), c_int, c_int, c_double], c_int)
Mix_FadeInChannel = lambda channel, chunk, loops, ms: Mix_FadeInChannelTimed(channel, chunk, loops, ms, -1)
Mix_FadeInChannelTimed = _bind("Mix_FadeInChannelTimed", [c_int, POINTER(Mix_Chunk), c_int, c_int, c_int], c_int)
Mix_Volume = _bind("Mix_Volume", [c_int, c_int], c_int)
Mix_VolumeChunk = _bind("Mix_VolumeChunk", [POINTER(Mix_Chunk), c_int], c_int)
Mix_VolumeMusic = _bind("Mix_VolumeMusic", [c_int], c_int)
Mix_HaltChannel = _bind("Mix_HaltChannel", [c_int], c_int)
Mix_HaltGroup = _bind("Mix_HaltGroup", [c_int], c_int)
Mix_HaltMusic = _bind("Mix_HaltMusic", None, c_int)
Mix_ExpireChannel = _bind("Mix_ExpireChannel", [c_int, c_int], c_int)
Mix_FadeOutChannel = _bind("Mix_FadeOutChannel", [c_int, c_int], c_int)
Mix_FadeOutGroup = _bind("Mix_FadeOutGroup", [c_int, c_int], c_int)
Mix_FadeOutMusic = _bind("Mix_FadeOutMusic", [c_int], c_int)
Mix_FadingMusic = _bind("Mix_FadingMusic", None, Mix_Fading)
Mix_FadingChannel = _bind("Mix_FadingChannel", [c_int], Mix_Fading)
Mix_Pause = _bind("Mix_Pause", [c_int])
Mix_Resume = _bind("Mix_Resume", [c_int])
Mix_Paused = _bind("Mix_Paused", [c_int], c_int)
Mix_PauseMusic = _bind("Mix_PauseMusic")
Mix_ResumeMusic = _bind("Mix_ResumeMusic")
Mix_RewindMusic = _bind("Mix_RewindMusic")
Mix_PausedMusic = _bind("Mix_PauseMusic", None, c_int)
Mix_SetMusicPosition = _bind("Mix_SetMusicPosition", [c_double], c_int)
Mix_Playing = _bind("Mix_Playing", [c_int], c_int)
Mix_PlayingMusic = _bind("Mix_PlayingMusic", None, c_int)
Mix_SetMusicCMD = _bind("Mix_SetMusicCMD", [c_char_p], c_int)
Mix_SetSynchroValue = _bind("Mix_SetSynchroValue", [c_int], c_int)
Mix_GetSynchroValue = _bind("Mix_GetSynchroValue", None, c_int)
Mix_SetSoundFonts = _bind("Mix_SetSoundFonts", [c_char_p], c_int)
Mix_GetSoundFonts = _bind("Mix_GetSoundFonts", None, c_char_p)
soundfont_function = CFUNCTYPE(c_int, c_char_p, c_void_p)
Mix_EachSoundFont = _bind("Mix_EachSoundFont", [soundfont_function, c_void_p], c_int)
Mix_GetChunk = _bind("Mix_GetChunk", [c_int], POINTER(Mix_Chunk))
Mix_CloseAudio = _bind("Mix_CloseAudio")
Mix_SetError = SDL_SetError
Mix_GetError = SDL_GetError
