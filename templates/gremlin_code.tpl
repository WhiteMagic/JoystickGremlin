import importlib
import gremlin

# Import custom modules
% for entry in module_imports:
${entry} = gremlin.util.load_module("${entry}")
% endfor