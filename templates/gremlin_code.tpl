import importlib
import gremlin

# Import custom modules
% for entry in profile.imports:
${entry} = gremlin.util.load_module("${entry}")
% endfor