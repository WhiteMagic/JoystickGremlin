<%namespace name="util" module="templates.functions"/>\
import importlib
import gremlin

# Import custom modules
% for entry in profile.imports:
${entry} = gremlin.util.load_module("${entry}")
% endfor

# Setup axis merging
% for i, merge_axis in enumerate(profile.merge_axes):
<%include
    file="merge_axis_callback.tpl"
    args="
        entry=merge_axis,
        decorator_data=decorators,
        index=i
    "
/>
% endfor