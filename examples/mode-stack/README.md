Introduction
============
This document tries to describe what can be done with mode stack implementation. It is a hack around the current implementation, but hopefully it describes what it provides well enough so a similar functionality can get implemented in r14 and beyond.

JG r13 supports switching modes, temporary mode switching and switching to previous mode. This is great, but in certain situations more flexibility is required. As a demonstration an F-16 profile will be used.

F-16 has 3 major modes: NAV, AA, AG. It also has 2 override modes: AA-DOGFIGHT-OVERRIDE, AA-MISSILE-OVERRIDE.
Let's create modes for each: NAV, AA, AG, AA-DF, AA-MIS. To demonstrate what mode stack is capable let's
assume the following narrative:

*A pilot is flying in NAV mode and switches to AG mode. Performs ground reconnaissance and is bugged
by a threat. The RWR shows the threat is close, so the pilot switches to AA-MIS mode and engages.
After the engagement pilot flips the AA-MIS switch back to center and resumes AG reconnaissance.
When he's finished, he clicks AG again and resumes NAV and flies home.*

Let's assume all buttons available to us are non-latching type, which means
that they return to the original position. FYI, in F-16, AG is non-latching, AA-MIS is latching (AFAIK).

To support the narrative above JG r13 profile would have to look like this:
(there might be other possibilities too, but require programming or extra
configuration steps).
- NAV mode
    - a button A to switch to AG mode
    - a button O to switch to AA-MIS mode
- AG mode
    - a button O to switch to AA-MIS mode
    - a button A to switch to NAV mode
- AA-MIS mode
    - a button O to switch to AG mode

A sim-pilot would start in NAV mode, then:
1. press A button in NAV mode to get to AG mode
2. press O button in AG mode to get to AA-MIS mode
3. press O button in AA-MIS mode to get back to AG mode
4. press A button in AG mode to get back to NAV mode

That's simple, right? Well, what happens if button O is pressed while mode is NAV? It switches to AA-MIS, good. But when you press it again to return to NAV, it goes to AG mode. Not good.

What about switch to previous mode or temporary switch mode? If you have non-latching buttons you either need to hold them for temporary mode switch to be useful (think of it as a SHIFT button). Switch to previous mode is useful, but only in simple scenarios. Let's setup the same
scenario using switch to previous mode:

- NAV mode
    - a button A to switch to AG mode
    - a button O to switch to AA-MIS mode
- AG mode
    - a button O to switch to AA-MIS mode
    - a button A to switch previous mode
- AA-MIS mode
    - a button O to switch to previous mode

A sim-pilot would start in NAV mode, then:
1. press A button in NAV mode to get to AG mode
2. press O button in AG mode to get to AA-MIS mode
3. press O button in AA-MIS mode to get back to AG mode, *good*
4. press A button in AG mode to get back to NAV mode, but would end up in AA-MIS mode, *not-good*.

JG mode stack comes to the rescue! The same profile would work with mode stack because it keeps
a track multiple previous modes. It works as a stack - as modes are switched to, they are added
to the stack, as they are switched to previous mode, they're popped from the stack.

- NAV mode
    - a button A to switch to AG mode
    - a button O to switch to AA-MIS mode (just for demonstrative purposes)
- AG mode
    - a button O to switch to AA-MIS mode
    - a button A to switch previous mode
- AA-MIS mode
    - a button O to switch to previous mode

A sim-pilot would start in NAV mode, then:
1. press A button in NAV mode to get to AG mode, and mode stack contain single mode: NAV
2. press O button in AG mode to get to AA-MIS mode, and mode stack would contain two mode elements: NAV, AG
3. press O button in AA-MIS mode to get back to AG mode, and mode stack
    would contain a single element: NAV
4. press A button in AG mode to get back to NAV mode, and mode stack
    would be empty - *yaay!!*


Temporary modes
===============
mode stack also supports stacking multiple temporary modes and as the buttons for temporary modes get depressed
they are removed from the stack. If they're depressed in random order the mode will return to the original mode
before the temporary modes were switched to.

Assume the mode stack was: NAV, *TEMP MODE1, *TEMP MODE2
Then TEMP MODE1 button is released, the mode stack is: NAV, *TEMP MODE2
When TEMP MODE2 button is released, the mode stack is NAV

Mode cycles
===========
When mode cycles are used the mode stack keeps a track of modes that were cycled too and keeps rotating them
so the stack does not grow to tall. Assume we have 2 modes in the cycle list: AA-MIS, AA-DF.
Say mode stack is NAV, CYCLED AA-MIS, CYCLED AA-DF. If you press the button to cycle the modes AA-MIS/AA-DF again
then the AA-MIS would be chosen and mode stack becomes: NAV, AA-DF, AA-MIS. Pressing the cycle again chooses
AA-DF mode and mode stack becomes: NAV, AA-MIS, AA-DF.







