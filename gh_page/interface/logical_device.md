---
title: Logical Device
parent: Interface
nav_order: 3
---

# Logical Device

Gremlin has an internal fake device, known as *Logical Device* that is capable of representing an infinite number of axis, buttons, and hats. This fake device is only visible inside of Gremlin but can be used to combine multiple axes, store logical state, and things I haven't thought of.

{: .text-center }
![Logical Device]({{ site.baseurl }}/assets/images/logical_device.png)

The *Logical Deivce* is shown in the list of device tabs and functions like any other physical device in that actions can be assigned to it and will be executed as usual. The difference is that the user can add any number of inputs to this device and name them to their liking.

One can map all physical device inputs to logical device inputs and then have these send the events on to vJoy devices or keyboard keys. There may be some slight overhead due to the indirection of an additional event but that should be negligable.

A good example of where the *Logical Device* is needed is when one wants to merge two axes but one or both axis need to be filtered or modified in some way, for example inverted with a response curve, before the merge. A *Merge Axis* action requires two axes as inputs and cannot perform actions before consuming the data from the axes. Thus the following works:

- Apply response curve and map to logical device to the physical axis
- Assign the logical device axis to the merge axis action
- Add a map to vJoy action to the merge axis action

The image below illustrates how such a setup would look like.

![Merge axis with logical device example]({{ site.baseurl }}/assets/images/logical_device_example.png)
{: .text-center }