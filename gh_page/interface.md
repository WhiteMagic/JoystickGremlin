---
title: Interface
nav_order: 4
---

# Interface

In the following the various components of the user interface are introduced and their usage described. The UI should be sufficient for most common use cases. However, if functionality is missing, user created modules can provide these.

The following is a short overview of the different components that make up the main user interface, shown in the following image.

{: .text-center }
![Main Window]({{ site.baseurl }}/assets/images/joystick_gremlin_main_window_numbered.png)<br>
*Joystick Gremlin UI*

1. The menu bar gives access to typical profile operations and [tools]({{ site.baseurl }}/interface/tools).
1. The toolbar holds the most commonly used operations, from left to right:
    - Create a new profile.
    - Save the current profile.
    - Load an existing profile.
    - Open the [Input Viewer]({{ site.baseurl }}/interface/tools#input-viewer).
    - Open the [Options]({{ site.baseurl }}/interface/options).
    - Activate and deactivate Joystick Gremlin.
1. *Configuring mode* selects the [Mode]({{ site.baseurl }}/interface/modes) whose actions are being edited.
1. Each tab represents a device. Every connected physical device has its own tab, followed by the *Keyboard* tab, and the [Logical Device]({{ site.baseurl }}/interface/logical_device) tab.
1. The *Scripts* tab manages [user scripts]({{ site.baseurl }}/interface/scripts) and the *Settings* tab holds [profile specific]({{ site.baseurl }}/interface/profile_settings) settings.
1. List all inputs of the selected device. Each entry shows the input's name, actions associated with it, and a description. These things can be changed in the options.
1. The main part of the UI shows the selected input's action sequences and allows configuring the [actions]({{ site.baseurl }}/interface/actions) to execute when the input is used.
1. The status bar shows whether a profile is running or paused, the mode being executed, and the mode being edited.
