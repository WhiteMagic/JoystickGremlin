---
title: FAQ
parent: Help
nav_order: 1
---

# Frequently Asked Questions

## The game does not see Joystick Gremlin inputs, only the original joystick ones.

This will happen quite often as Joystick Gremlin cannot hide the physical devices inputs. The most reliable way to solve this is to use [HidHide](https://github.com/nefarius/HidHide){:target="_blank"} to hide physical devices from the game.

## How to verify that Joystick Gremlin produces the desired output?

The simplest way, which doesn't require any additional tools, is to use the Windows game controller program, which can be launched by running <kbd>joy.cpl</kbd>. To see the output simply open the dialog for the desired vJoy device. One drawback of this tool is that it requires focus to show anything which can be a bit cumbersome at times. Gremlin also has its own input visualizer *Tools -> Input Viewer*.

## Macros don't work in-game

The most likely cause for this is that the game was launched with administrator privileges while Joystick Gremlin was launched with normal user privileges. As the macro system injects key presses into the Windows event system, Joystick Gremlin has to have the same or higher privilege level as the receiving application. As such if the game is run as administrator then Joystick Gremlin needs to be run as administrator as well.

Another reason why macros might not work is that they send key presses too fast. By default Gremlin adds a small delay, however, should this delay be too small the game might not register these presses. The *Settings* tab allows changing this default pause duration and increasing it might help in some cases.

## Macro doesn't produce a stream of characters

A common misconception is that when a key is held down that this will result in a sequence of key presses. This stems from the fact that holding a physical key down a bunch of characters will appear in a text editor etc. What happens in reality is that Windows will, behind the scene, emit these characters at a set frequency, despite there being only one physical key press event.

This means that you should not expect to see a macro that holds down a key to result in a bunch of characters appearing in a text field, but only one. This is the correct behavior and games expect and handle this properly. To check if a macro sends the correct key strokes you should use a keyboard testing program such as [https://keyboardtester.io/tester/](https://keyboardtester.io/tester/){:target="_blank"}, or any other one that a search turns up, to verify keys are pressed and released as expected.