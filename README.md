Joystick Gremlin
================

Introduction
------------

**Getting Help:** If you have issues running Gremlin or questions on how to
make certain things work, the best place to ask for help is in the
#joystick-gremlin channel on the HOTAS discord which can be found here
https://discord.gg/szqaJE7.

Joystick Gremlin is a program that allows the configuration of joystick like
devices, similar to what CH Control Manager and Thrustmaster's T.A.R.G.E.T. do
for their respectively supported joysticks. However, Joystick Gremlin works
with any device be it from different manufacturers or custom devices that
appear as a joystick to Windows. Joystick Gremlin uses the virtual joysticks
provided by vJoy to map physical to virtual inputs and apply various other
transformations such as response curves to analogue axes. In addition to
managing joysticks, Joystick Gremlin also provides keyboard macros, a flexible
mode system, scripting using Python, and many other features.

The main features are:
- Works with arbitrary joystick like devices
- User interface for common configuration tasks
- Merging of multiple physical devices into a single virtual device
- Axis response curve and dead zone configuration
- Arbitrary number of modes with inheritance and customizable mode switching
- Keyboard macros for joystick buttons and keyboard keys
- Python scripting

Joystick Gremlin provides a graphical user interface which allows commonly
performed tasks, such as input remapping, axis response curve setups, and macro
recording to be performed easily. Functionality that is not accessible via the
UI can be implemented through custom modules.

Getting Starget
---------------

For a list of dependencies and an overview of how to install and use Gremlin take a look at the [Manual](https://whitemagic.github.io/JoystickGremlin/overview).


Used Software & Other Sources
-----------------------------
Joystick Gremlin uses the following software and resources:

- [Python 3.7](https://www.python.org)
- [PySide6](https://www.qt.io/qt-for-python)
- [PyWin32](http://sourceforge.net/projects/pywin32)
- [Reportlab](https://www.reportlab.com/)
- [PyTest](https://docs.pytest.org/en/latest/)
- [PyInstaller](http://www.pyinstaller.org/)
- [vJoy](https://github.com/jshafer817/vJoy/releases/tag/v2.1.9.1)
- [Modern UI Icons](http://modernuiicons.com/)

Currently the 32bit version of Python is needed and the following packages
should be installed via PiP to get the source running:


Generating the MSI Installer
----------------------------

The job of turning the Python code in a windows executable and
packaging everything up into an installable MSI file is performed
by [pyinstaller](http://www.pyinstaller.org/) and
[wix](http://wixtoolset.org/). The steps needed to build the code
and assemble it into the installer is automated using a batch
script and can be run as:
  ```
  deploy.bat
  ```
To simply generate the executable code without the MSI installer the
following command can be used:
  ```
  pyinstaller -y --clean joystick_gremlin.spec
  ```
