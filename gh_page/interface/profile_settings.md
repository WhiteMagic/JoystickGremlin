---
title: Profile Settings
parent: Interface
nav_order: 5
---

# Profile Settings

Options that could change based on the specific profile can be set in the *Settings* tab. This allows you to configure the following aspects:

{: .text-center }
![Profile Settings]({{ site.baseurl }}/assets/images/ui/profile_settings.png)<br>
*The settings tab allows configuring options specific to the current profile.*


## Startup Mode

When Gremlin is activated an initial mode has to be selected. This drop down allows you to select one of the modes that exist in the profile or one of two heuristics.

<dl>
    <dt>Use Heuristic</dt>
    <dd>Selects the first mode in alphabetical order that has no parent.</dd>
    <dt>Last Active</dt>
    <dd>Selects the mode that was active the last time the profile was used.</dd>
</dl>

## Macro Default Delay

When a macro action contains more than one event to emit, Gremlin will inject a small delay between subsequent actions that do not contain a pause between them. This is to ensure games register the events correctly. However, the duration of this pause may need to be tuned or even disabled entirely. The value in this field allows specifying this duration in seconds.

## vJoy Behavior

Gremlin is not the only program using vJoy and thus there are instances where it is desirable that Gremlin treats a vJoy device not as an output but rather as an input device. By turning a vJoy device into an input device Gremlin will no longer attempt to acquire or use that device for output. Instead the vJoy device will be listed as if it was a physical device and can have action sequences assigned to it as well. This will remove the particular vJoy device from the *Map to vJoy* options list as well.

{: .note }
By design a single vJoy device can only be "owned" by one process. Thus it is impossible for Gremlin and another program to share access to the same vJoy device. Gremlin only acquires devices that it needs when it needs them to play nicely with other programs also using vJoy devices. However, not all programs behave this well.

{: .warning }
Marking all vJoy devices as inputs is possible. However, then Gremlin can not be used to emit joystick events that will be seen by a game.

## vJoy Initial Values

By default Gremlin initializes all vJoy axes of vJoy devies it controls to 0. In some scenarios this is not the desired default value, in which case the desired default value can be configured here.
