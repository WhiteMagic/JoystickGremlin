import importlib
import gremlin
from vjoy.vjoy import AxisName

% for entry in user_imports:
${entry} = gremlin.util.load_module("${entry}")
% endfor

tts = gremlin.tts.TextToSpeech()