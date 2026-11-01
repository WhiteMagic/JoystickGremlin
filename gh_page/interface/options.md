---
title: Options
parent: Interface
nav_order: 6
---

# Options

The options window shows the various options that Gremlin allows to be configured. Each entry has a short explanation of what the particular option does.

{: .text-center }
![Options Window]({{ site.baseurl }}/assets/images/ui/options.png)<br>
*The options window exposes all the settings one can change in Gremlin.*

The options are grouped into three sections which contain the following aspects:
<dl>
    <dt>Global</dt>
    <dd>Contains general settings affecting Gremlin's overall behavior, described below.</dd>
    <dt>Action</dt>
    <dd>Contains all settings relating to the behavior of specific actions.</dd>
    <dt>Profile</dt>
    <dd>Contains all settings revolving around profile auto loading.</dd>
</dl>

The following global options are worth pointing out.

<dl>
    <dt>Color theme selection</dt>
    <dd>Selects the color theme of the UI, which can be dark, light, or zenburn.</dd>
    <dt>Ui scale</dt>
    <dd>Scales the UI to 100, 150, or 200 percent.</dd>
    <dt>Close to tray</dt>
    <dd>Closing the Gremlin window hides it in the system tray rather than terminating Gremlin. Gremlin is then quit via the tray icon's menu.</dd>
    <dt>Minimize to tray</dt>
    <dd>Minimizes the Gremlin window to the system tray instead of the taskbar.</dd>
    <dt>Input highlighting</dt>
    <dd>Using an input on a physical device selects that input in the UI, if the device's tab is the active one.</dd>
    <dt>Refresh axis on activation</dt>
    <dd>Upon activating a profile the known state of the physical devices is used to perform the actions associated with their axes, instead of waiting for the axes to be moved.</dd>
    <dt>Use legacy dill</dt>
    <dd>Uses the legacy input library instead of the new one, in case of problems with the latter. Changing this requires restarting Gremlin.</dd>
</dl>
