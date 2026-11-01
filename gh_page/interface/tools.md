---
title: Tools
parent: Interface
nav_order: 7
---

# Tools

Gremlin comes with a variety of tools to both manage Gremlin and its profiles but also to introspect the behavior.

## Input Viewer

{: .text-center }
![Input Viewer]({{ site.baseurl }}/assets/images/ui/input_viewer.png)

The Input Viewer shows the inputs received by Gremlin from all sources. It can show axes values either as a time series or the current state while button and hats can be visualized as their current state.


## Calibration

{: .text-center }
![Calibration]({{ site.baseurl }}/assets/images/ui/calibration.png)

The calibration dialog allows calibrating the physical devices used by Gremlin. The calibration information is applied to every reading Gremlin receives from the physical device before processing it further. The dialog shows the raw as well as the post-calibration values directly in the UI. The values can be recorded simply by moving the axis with the input fields permitting manual adjustments to the recorded values.


## Device Information

{: .text-center }
![Device Information]({{ site.baseurl }}/assets/images/ui/device_information.png)

Lists the physical and vJoy devices Gremlin sees along with their number of axes, buttons, and hats, as well as their identifiers.


## View Logs

{: .text-center }
![Log Viewer]({{ site.baseurl }}/assets/images/ui/log_viewer.png)

Shows the log messages of the current session. The *System* tab holds the messages of Gremlin itself while the *User* tab holds the ones written by user scripts. The view automatically updates with new log messages.


## Auto Mapper

{: .text-center }
![Auto Mapper]({{ site.baseurl }}/assets/images/ui/auto_mapper.png)

The auto mapper tool allows creating basic 1 to 1 mappings that add *Map to vJoy* actions between the selected physical input and the selected vJoy output. Select the physical devices and vJoy devices to use, as well as the mode to create the mappings in, with *Select Mode*, before clicking the "Create 1:1 mappings" button. The two options enable the following behaviors.

<dl>
    <dt>Overwrite non-empty physical inputs</dt>
    <dd>Normally inputs with configured actions are skipped, if this option is activated the existing actions are removed and a new mapping is added.</dd>
    <dt>Repeat vJoy devices</dt>
    <dd>If more vJoy outputs are required than available, this option will reuse already assigned vJoy inputs.</dd>
</dl>


## Swap Devices

{: .text-center }
![Swap Devices]({{ site.baseurl }}/assets/images/ui/swap_devices.png)

This tool allows assigning contents from a profile to an existing physical device. It can be used when migrating to a new machine where device identifiers have changed or when using a profile made by someone else. The assigning of profile mappings to a device only allows the mapping to a device that has the correct number of inputs required by the configuration.

Pick the source device that exists in a profile and the target device that is currently connected, then press the "Swap Bindings" button.


## Help Menu

The *Help* menu holds the *Release Notes*, which are also shown the first time a new release is started, and *About*, which shows the version of Gremlin in use.
