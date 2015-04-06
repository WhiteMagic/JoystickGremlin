import argparse
import ctypes
import importlib
import logging
import os
import signal
import sys

os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.realpath(sys.argv[0]))
import sdl2
import sdl2.ext
import sdl2.hints

from PyQt5 import QtWidgets

from gremlin.event_handler import EventHandler, EventListener
import gremlin


def abort_handler(app, signal, frame):
    """Terminates the even listener loop as well as the Qt application.

    :param app the qt application to terminate
    :param signal the received signal
    :param frame the frame from which the signal originated
    """
    EventListener().terminate()
    app.quit()


def main():
    """Main application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Joystick Gremlin")
    parser.add_argument("folder")
    parser.add_argument("modules", nargs="+")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        filename=os.path.join(gremlin.util.script_path(), "debug.log"),
        format="%(asctime)s %(levelname)10s %(message)s",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.DEBUG
    )

    # Initialize SDL2
    sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
    sdl2.SDL_SetHint(
                sdl2.hints.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,
                ctypes.c_char_p(b"1")
    )
    sdl2.ext.init()

    # Setup device key generator based on whether or not we have
    # duplicate devices connected.
    gremlin.util.setup_duplicate_joysticks()

    # Add user provided module path to the system path and load the
    # provided modules
    sys.path.insert(0, args.folder)
    try:
        for module in args.modules:
            importlib.import_module(module)
    except ImportError as e:
        print("Failed to import some modules, {}".format(str(e)))
        return 1

    # Setup event listening and handling system
    el = EventListener()
    kb = gremlin.input_devices.Keyboard()
    eh = EventHandler()

    # Add input device plugins for the callbacks
    eh.add_plugin(gremlin.input_devices.JoystickPlugin())
    eh.add_plugin(gremlin.input_devices.VJoyPlugin())
    eh.add_plugin(gremlin.input_devices.KeyboardPlugin())

    # Go through all callbacks and install them
    callback_count = 0
    for device_id, modes in gremlin.input_devices.callback_registry.registry.items():
        for mode, callbacks in modes.items():
            for event, callback_list in callbacks.items():
                for callback in callback_list:
                    eh.add_callback(
                        device_id,
                        mode,
                        event,
                        callback[0],
                        callback[1]
                    )
                    callback_count += 1
    print("Loaded {:d} callbacks".format(callback_count))

    # Connect event processing functions
    el.keyboard_event.connect(eh.process_event)
    el.joystick_event.connect(eh.process_event)
    el.keyboard_event.connect(kb.keyboard_event)

    # Start QT event loop and hook the abort signal handler up
    app = QtWidgets.QApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda x, y: abort_handler(app, x, y))
    app.exec_()

    # Clean everything up
    el.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())