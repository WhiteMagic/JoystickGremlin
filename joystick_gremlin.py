# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Main UI of JoystickGremlin.
"""

import argparse
import ctypes
import logging
import os
import sys
import time
import traceback

from pathlib import Path
from typing import Any, Dict

# Import QtMultimedia so pyinstaller doesn't miss it
from PySide6 import QtCore, QtGui, QtQml, QtQuick, QtWidgets

import resources

import dill
import vjoy.vjoy
from gremlin.config import Configuration
from gremlin.types import PropertyType

# Figure out the location of the code / executable and change the working
# directory accordingly
install_path = os.path.normcase(os.path.dirname(os.path.abspath(sys.argv[0])))
os.chdir(install_path)

# Setting some global QT configurations
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Universal"
# os.environ["QT_QUICK_CONTROLS_MATERIAL_VARIANT"] = "Normal"
os.environ["QT_QUICK_CONTROLS_UNIVERSAL_THEME"] = "Light"
# os.environ["QT_QUICK_CONTROLS_HOVER_ENABLED"] = "true"
# os.environ["QML_IMPORT_TRACE"] = "1"
# os.environ["QSG_RHI"] = "1"

# Path mangling to ensure Gremlin can run indepent of the CWD and
# ensure configuration folder is created in time
import gremlin.util
sys.path.insert(0, gremlin.util.userprofile_path())
gremlin.util.setup_userprofile()

import gremlin.config
import gremlin.error
import gremlin.device_initialization
import gremlin.plugin_manager
import gremlin.types
import gremlin.signal

import gremlin.ui.backend
import gremlin.ui.config


def configure_logger(config: Dict[str, Any]) -> None:
    """Creates a new logger instance.

    Args:
        config configuration information for the new logger
    """
    logger = logging.getLogger(config["name"])
    logger.setLevel(config["level"])
    handler = logging.FileHandler(config["logfile"])
    handler.setLevel(config["level"])
    formatter = logging.Formatter(config["format"], "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.debug("-" * 80)
    logger.debug(time.strftime("%Y-%m-%d %H:%M"))
    logger.debug("Starting Joystick Gremlin R14")
    logger.debug("-" * 80)


def exception_hook(exception_type, value, trace) -> None:
    """Logs any uncaught exceptions.

    Args:
        exception_type: type of exception being caught
        value: content of the exception
        trace: the stack trace which produced the exception
    """
    msg = "Uncaught exception:\n"
    msg += " ".join(traceback.format_exception(exception_type, value, trace))
    logging.getLogger("system").error(msg)
    gremlin.util.display_error(msg)


def shutdown_cleanup() -> None:
    """Handles cleanup before terminating Gremlin."""
    # Terminate potentially running EventListener loop
    event_listener = gremlin.event_handler.EventListener()
    event_listener.terminate()

    # Terminate profile runner
    backend = gremlin.ui.backend.Backend()
    backend.runner.stop()

    # Relinquish control over all VJoy devices used
    vjoy.vjoy.VJoyProxy.reset()


def register_config_options() -> None:
    cfg = gremlin.config.Configuration()

    cfg.register(
        "global", "internal", "last_mode",
        PropertyType.String, "Default",
        "Name of the last active mode", {}
    )
    cfg.register(
        "global", "internal", "last_profile",
        PropertyType.String, "",
        "Most recently used profile", {}
    )
    cfg.register(
        "global", "internal", "recent_profiles",
        PropertyType.List, [],
        "List of recently opened profiles", {}
    )
    cfg.register(
        "global", "general", "plugin_directory",
        PropertyType.String, "",
        "Directory containing additional action plugins", {},
        True
    )


def make_gremlin_app(argv):
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        help="Path to the profile to load on startup",
    )
    parser.add_argument(
        "--enable",
        help="Enable Joystick Gremlin upon launch",
        action="store_true"
    )
    parser.add_argument(
        "--start-minimized",
        help="Start Joystick Gremlin minimized",
        action="store_true"
    )
    args, _ = parser.parse_known_args(argv)

    # Configure logging for system and user events
    configure_logger({
        "name": "system",
        "level": logging.DEBUG,
        "logfile": os.path.join(gremlin.util.userprofile_path(), "system.log"),
        "format": "%(asctime)s %(levelname)10s %(message)s"
    })
    configure_logger({
        "name": "user",
        "level": logging.DEBUG,
        "logfile": os.path.join(gremlin.util.userprofile_path(), "user.log"),
        "format": "%(asctime)s %(message)s"
    })
    syslog = logging.getLogger("system")

    # Setup the configuration system
    register_config_options()

    # Show unhandled exceptions to the user when running a compiled version
    # of Joystick Gremlin
    executable_name = os.path.split(sys.executable)[-1]
    if executable_name == "joystick_gremlin.exe":
        sys.excepthook = exception_hook


    # +-------------------------------------------------------------------------
    # | Initialize QT system
    # +-------------------------------------------------------------------------

    # debug = QtQml.QQmlDebuggingEnabler()
    QtCore.QLoggingCategory.setFilterRules("qt.qml.binding.removal.info=true")

    # Initialize QT components
    #QtWebEngine.QtWebEngine.initialize()

    # Prevent blurry fonts that Qt seems to like
    QtQuick.QQuickWindow.setTextRenderType(
        QtQuick.QQuickWindow.NativeTextRendering
    )
    # Use software rendering to prevent flickering on variable refresh rate
    # displays
    # QtQuick.QQuickWindow.setSceneGraphBackend("software")
    QtQuick.QQuickWindow.setGraphicsApi(QtQuick.QSGRendererInterface.OpenGL)

    # Create user interface
    app_id = u"joystick.gremlin"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    app = QtWidgets.QApplication(argv)
    app.setWindowIcon(QtGui.QIcon("gfx/icon.png"))
    app.setApplicationDisplayName("Joystick Gremlin")

    # Configure QSettings to keep QT happy
    app.setOrganizationName("H2IK")
    app.setOrganizationDomain("https://whitemagic.github.io/JoystickGremlin/")
    app.setApplicationName("Joystick Gremlin")

    # Change application wide font
    app.setFont(QtGui.QFont("Segoe UI", 11))

    # Ensure joystick devices are correctly setup
    dill.DILL.init()
    gremlin.device_initialization.joystick_devices_initialization()

    # Create application and UI engine
    engine = QtQml.QQmlApplicationEngine(parent=app)
    engine.addImportPath(".")
    QtCore.QDir.addSearchPath(
        "core_plugins",
        gremlin.util.resource_path("action_plugins/")
    )
    cfg = Configuration()
    user_plugins_path = Path(cfg.value("global", "general", "plugin_directory"))
    if user_plugins_path.is_dir():
        QtCore.QDir.addSearchPath(
            "user_plugins",
            str(user_plugins_path)
        )


    # +-------------------------------------------------------------------------
    # | Register data types for use in QML
    # +-------------------------------------------------------------------------

    # Create and register backend and signal objects
    backend = gremlin.ui.backend.Backend(engine)
    backend.newProfile()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("uiState", backend.ui_state)
    engine.rootContext().setContextProperty("signal", gremlin.signal.signal)

    # Load plugin code and UI elements
    syslog.info("Initializing plugins")
    gremlin.plugin_manager.PluginManager()

    # Purgre configuration options that have not been registered
    cfg.purge_unused()


    # +-------------------------------------------------------------------------
    # | Start Gremlin UI
    # +-------------------------------------------------------------------------

    # Load icon fonts
    if QtGui.QFontDatabase.addApplicationFont(":/BootstrapIcons") < 0:
        syslog.error("Failed to load BootstrapIcons")

    # Initialize main UI
    engine.load(QtCore.QUrl.fromLocalFile(
        gremlin.util.resource_path("qml/Main.qml"))
    )
    if not engine.rootObjects():
        sys.exit(-1)

    # Check if vJoy is properly setup and if not display an error
    # and terminate Gremlin
    # try:
    #     syslog.info("Checking vJoy installation")
    #     vjoy_working = len([
    #         dev for dev in gremlin.device_initialization.joystick_devices()
    #         if dev.is_virtual
    #     ]) != 0
    #
    #     if not vjoy_working:
    #         logging.getLogger("system").error(
    #             "vJoy is not present or incorrectly setup."
    #         )
    #         raise gremlin.error.GremlinError(
    #             "vJoy is not present or incorrectly setup."
    #         )
    #
    # except (gremlin.error.GremlinError, dill.DILLError) as e:
    #     error_display = QtWidgets.QMessageBox(
    #         QtWidgets.QMessageBox.Critical,
    #         "Error",
    #         e.value,
    #         QtWidgets.QMessageBox.Ok
    #     )
    #     error_display.show()
    #     app.exec_()
    #
    #     vjoy.vjoy.VJoyProxy.reset()
    #     event_listener = gremlin.event_handler.EventListener()
    #     event_listener.terminate()
    #     sys.exit(0)

    # Load the profile specified by the user on the command line, otherwise
    # attempt to load the previously loaded profile
    if args.profile is not None and os.path.isfile(args.profile):
        backend.loadProfile(args.profile)
    else:
        last_profile = Path(Configuration().value(
            "global", "internal", "last_profile")
        )
        if last_profile.is_file():
            backend.loadProfile(str(last_profile))

    if args.enable:
        backend.activate_gremlin(True)
    if args.start_minimized:
        backend.minimize()

    # Run UI
    syslog.info("Gremlin UI launching")
    app.aboutToQuit.connect(shutdown_cleanup)
    cfg.ensure_watcher_running()
    return app


if __name__ == "__main__":
    app = make_gremlin_app(sys.argv)
    app.exec()
    syslog = logging.getLogger("system")
    syslog.info("Gremlin UI terminated")

    syslog.info("Terminating Gremlin")
    sys.exit(0)
