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

import linput
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

    # Clean up Linux input/output devices
    linput.shutdown()


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


def parse_arguments(argv):
    """Parse command line arguments.

    Args:
        argv: Command line parameters

    Returns:
        Parsed command line arguments
    """
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
    return args


def setup_logging():
    """Configure system and user logging.

    Returns:
        System logger instance
    """
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
    return logging.getLogger("system")


def setup_exception_handling():
    """Configure exception handling for compiled executables."""
    executable_name = os.path.split(sys.executable)[-1]
    if executable_name == "joystick_gremlin.exe":
        sys.excepthook = exception_hook


def initialize_qt_rendering():
    """Configure Qt rendering and graphics settings."""
    QtCore.QLoggingCategory.setFilterRules("qt.qml.binding.removal.info=true")
    QtQuick.QQuickWindow.setTextRenderType(
        QtQuick.QQuickWindow.NativeTextRendering
    )
    QtQuick.QQuickWindow.setGraphicsApi(QtQuick.QSGRendererInterface.OpenGL)


def create_qt_application(argv):
    """Create and configure Qt application.

    Args:
        argv: Command line parameters

    Returns:
        Configured QApplication instance
    """
    app_id = u"joystick.gremlin"
    app = QtWidgets.QApplication(argv)
    app.setWindowIcon(QtGui.QIcon("gfx/icon.png"))
    app.setApplicationDisplayName("Joystick Gremlin")
    app.setOrganizationName("H2IK")
    app.setOrganizationDomain("https://whitemagic.github.io/JoystickGremlin/")
    app.setApplicationName("Joystick Gremlin")
    return app


def initialize_devices():
    """Initialize joystick devices and input system."""
    linput.initialize()
    gremlin.device_initialization.joystick_devices_initialization()


def create_qml_engine(app):
    """Create and configure QML engine.

    Args:
        app: Qt application instance

    Returns:
        Configured QML engine
    """
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
    return engine


def register_backend(engine, syslog):
    """Register backend and UI components with QML.

    Args:
        engine: QML engine instance
        syslog: System logger

    Returns:
        Backend instance
    """
    backend = gremlin.ui.backend.Backend(engine)
    backend.newProfile()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("uiState", backend.ui_state)
    engine.rootContext().setContextProperty("signal", gremlin.signal.signal)

    syslog.info("Initializing plugins")
    gremlin.plugin_manager.PluginManager()

    cfg = Configuration()
    cfg.purge_unused()

    return backend


def load_ui(engine, syslog):
    """Load main UI and icon fonts.

    Args:
        engine: QML engine instance
        syslog: System logger

    Returns:
        True if UI loaded successfully
    """
    if QtGui.QFontDatabase.addApplicationFont(":/BootstrapIcons") < 0:
        syslog.error("Failed to load BootstrapIcons")

    engine.load(QtCore.QUrl.fromLocalFile(
        gremlin.util.resource_path("qml/Main.qml"))
    )
    return bool(engine.rootObjects())


def load_profile(backend, args):
    """Load profile from command line or last used.

    Args:
        backend: Backend instance
        args: Command line arguments
    """
    if args.profile is not None and os.path.isfile(args.profile):
        backend.loadProfile(args.profile)
    else:
        last_profile = Path(Configuration().value(
            "global", "internal", "last_profile")
        )
        if last_profile.is_file():
            backend.loadProfile(str(last_profile))


def apply_startup_options(backend, args, app, syslog):
    """Apply command line startup options.

    Args:
        backend: Backend instance
        args: Command line arguments
        app: Qt application
        syslog: System logger
    """
    if args.enable:
        backend.activate_gremlin(True)
    if args.start_minimized:
        backend.minimize()

    syslog.info("Gremlin UI launching")
    app.aboutToQuit.connect(shutdown_cleanup)


def make_gremlin_app(argv):
    """Create and configure the QT application instance used by Gremlin.

    Args:
        argv: Command line parameters

    Returns:
        Created QApplication instance configured for Gremlin
    """
    # Parse command line and configure system
    args = parse_arguments(argv)
    syslog = setup_logging()
    register_config_options()
    setup_exception_handling()

    # Initialize Qt system
    initialize_qt_rendering()
    app = create_qt_application(argv)

    # Initialize devices and create UI engine
    initialize_devices()
    engine = create_qml_engine(app)

    # Register backend and load plugins
    backend = register_backend(engine, syslog)

    # Load and start UI
    if not load_ui(engine, syslog):
        sys.exit(-1)

    # Load profile and apply startup options
    load_profile(backend, args)
    apply_startup_options(backend, args, app, syslog)

    return app


if __name__ == "__main__":
    app = make_gremlin_app(sys.argv)
    app.exec()
    syslog = logging.getLogger("system")
    syslog.info("Gremlin UI terminated")

    syslog.info("Terminating Gremlin")
    sys.exit(0)
