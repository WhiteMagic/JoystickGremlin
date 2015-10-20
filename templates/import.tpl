import importlib
import gremlin
from vjoy.vjoy import AxisName

% for entry in user_imports:
${entry} = gremlin.util.load_module("${entry}")
% endfor

hat_direction_map = {
    ( 0,  0) : -1,
    ( 0,  1) :   0,
    ( 1,  1) :  45,
    ( 1,  0) :  90,
    ( 1, -1) : 135,
    ( 0, -1) : 180,
    (-1, -1) : 225,
    (-1,  0) : 270,
    (-1,  1) : 315,
}

tts = gremlin.tts.TextToSpeech()