# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import argparse
import ctypes
import logging
import logging.handlers
import os
import sys
import time
import traceback

from pathlib import Path
from typing import Any, Dict, List

# Import QtMultimedia so pyinstaller doesn't miss it.
from PySide6 import QtCore, QtGui, QtQml, QtQuick, QtWidgets

import resources

import dill
import vjoy.vjoy
from gremlin.config import Configuration
from gremlin.types import PropertyType

# Figure out the location of the code / executable and change the working
# directory accordingly.
install_path = os.path.normcase(os.path.dirname(os.path.abspath(sys.argv[0])))
os.chdir(install_path)

# Setting some global QT configurations.
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Universal"
# os.environ["QML_IMPORT_TRACE"] = "1"
# os.environ["QSG_RHI"] = "1"

# Path mangling to ensure Gremlin can run indepent of the CWD and
# ensure configuration folder is created in time.
import gremlin.util
sys.path.insert(0, gremlin.util.userprofile_path())
gremlin.util.setup_userprofile()

import gremlin.audio_player
import gremlin.config
import gremlin.error
import gremlin.device_initialization
import gremlin.event_handler
import gremlin.mode_manager
import gremlin.plugin_manager
import gremlin.types
import gremlin.signal

import gremlin.ui.backend
import gremlin.ui.option
import gremlin.ui.tools
import gremlin.ui.util


def configure_logger(config: Dict[str, Any]) -> None:
    """Creates a new logger instance.

    Args:
        config: configuration information for the new logger
    """
    logger = logging.getLogger(config["name"])
    logger.setLevel(config["level"])
    handler = logging.handlers.RotatingFileHandler(
        config["logfile"],
        maxBytes=1 * 1024 * 1024,
        backupCount=1
    )
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
    msg = " ".join(traceback.format_exception(exception_type, value, trace))
    logging.getLogger("system").error(f"Unhandled exception: {msg}")
    gremlin.signal.display_error("An unhandled exception occured.", msg)


def shutdown_cleanup() -> None:
    """Handles cleanup before terminating Gremlin."""
    # Terminate potentially running EventListener loop.
    gremlin.event_handler.EventListener().terminate()

    # Terminate profile runner.
    backend = gremlin.ui.backend.Backend()
    backend.runner.stop()
    backend.process_monitor.stop()

    # Relinquish control over all VJoy devices used.
    vjoy.vjoy.VJoyProxy.reset()

    gremlin.audio_player.AudioPlayer().stop()

def register_config_options() -> None:
    cfg = gremlin.config.Configuration()

    cfg.register(
        "global", "internal", "last-mode",
        PropertyType.String, "Default",
        "Name of the last active mode", {}
    )
    cfg.register(
        "global", "internal", "last-profile",
        PropertyType.String, "",
        "Most recently used profile", {}
    )
    cfg.register(
        "global", "internal", "recent-profiles",
        PropertyType.List, [],
        "List of recently opened profiles", {}
    )
    cfg.register(
        "global", "general", "plugin-directory",
        PropertyType.Path, "",
        "Directory containing additional action plugins", {"is_folder": True}, True
    )
    cfg.register(
        "global", "general", "action-priorities",
        PropertyType.List, [],
        "Priority order of the actions", {}, True
    )
    cfg.register(
        "global", "general", "device-change-behavior",
        PropertyType.Selection, "Reload",
        "Action Gremlin takes when a joystick is connected or disconnected.",
        {"valid_options": ["Disable", "Ignore", "Reload"]}, True
    )
    cfg.register(
        "global", "general", "dark-mode",
        PropertyType.Bool, False,
        "Use the dark mode UI (requires restart).", {}, True
    )
    cfg.register(
        "global", "general", "refresh-axis-on-activation",
        PropertyType.Bool, True,
        "Use known physical device state to perform actions using these values "
        "upon profile activation.", {}, True
    )
    cfg.register(
        "global", "general", "refresh-axis-on-mode-change",
        PropertyType.Bool, True,
        "Force an update of all axes by emitting axis events upon a mode change.",
        {}, True
    )
    cfg.register(
        "profile", "automation", "enable-auto-loading",
        PropertyType.Bool, False,
        "Enable the automatic loading and activation of profiles based on the "
        "specified executable and profile combinations.",
        {}, True
    )
    cfg.register(
        "profile", "automation", "remain-active-on-focus-loss",
        PropertyType.Bool, False,
        "Keep the profile active when the monitored executable loses focus and "
        "the newly focused executable does not have a profile assigned to it.",
        {}, True
    )
    cfg.register(
        "profile", "automation", "entries-auto-loading",
        PropertyType.List, [],
        "List of executable and profile combinations for automatic loading.",
        {}, False
    )


def configure_loggers() -> None:
    """Configures logging for system and user events."""
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


def update_action_priorities() -> None:
    cfg = gremlin.config.Configuration()
    key = ["global", "general", "action-priorities"]
    priorities = []
    if cfg.exists(*key):
        priorities = cfg.value(*key)
    priority_names = [v[0] for v in priorities]

    # Obtain the list of currently available plugins with an alphabetical
    # order for all but the most important actions.
    priority_actions = ["Map to vJoy", "Macro", "Response Curve"]
    plugin_names = [
        p.name for p in
        gremlin.plugin_manager.PluginManager().repository.values()
    ]
    plugin_names = [n for n in priority_actions if n in plugin_names] + \
        sorted([n for n in plugin_names if n not in priority_actions])

    for tag in plugin_names:
        if tag not in priority_names:
            priorities.append((tag, True))
    to_delete = []
    for i, tag in enumerate(priority_names):
        if tag not in plugin_names:
            to_delete.append(i)
    for idx in reversed(to_delete):
        del priorities[idx]

    cfg.set(*key, priorities)


class JoystickGremlinApp(QtWidgets.QApplication):

    def __init__(self, argv: List[str]) -> None:
        # Parse command line arguments.
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
        cmd_args, qt_argv = parser.parse_known_args(argv)

        # Run the parent constructor with remaining arguments.
        super().__init__(qt_argv)

        # Initialize various components.
        configure_loggers()
        self.syslog = logging.getLogger("system")
        register_config_options()

        # Ensure unhandled exceptions are shown to the user when running a
        # compiled version of Joystick Gremlin.
        executable_name = os.path.split(sys.executable)[-1]
        if executable_name == "joystick_gremlin.exe":
            sys.excepthook = exception_hook
        sys.excepthook = exception_hook

        # Initialize joystick device handling.
        self.syslog.info("Initializing joystick devices")
        dill.DILL.init()
        try:
            gremlin.device_initialization.joystick_devices_initialization()
        except gremlin.error.GremlinError as e:
            gremlin.signal.display_error(
                "Device initialization failed.", str(e)
            )
            sys.exit(0)

        self.initialize_qt()

        # Load plugin code and UI elements
        self.syslog.info("Initializing plugins")
        gremlin.plugin_manager.PluginManager()

        # Purge configuration options that have not been registered and update
        # the action priority information.
        self.cfg.purge_unused()
        update_action_priorities()

        # Initialize main UI.
        self.engine.load(QtCore.QUrl.fromLocalFile(
            gremlin.util.resource_path("qml/Main.qml"))
        )
        if not self.engine.rootObjects():
            sys.exit(-1)

        self.process_cmd_args(cmd_args)

        # Run UI.
        self.syslog.info("Gremlin UI launching")
        self.aboutToQuit.connect(shutdown_cleanup)

    def process_cmd_args(self, args: argparse.Namespace) -> None:
        # Load the profile specified by the user on the command line, otherwise
        # attempt to load the previously loaded profile
        if args.profile is not None and os.path.isfile(args.profile):
            self.backend.loadProfile(args.profile)
        else:
            last_profile = Path(Configuration().value(
                "global", "internal", "last-profile")
            )
            if last_profile.is_file():
                self.backend.loadProfile(str(last_profile))

        if args.enable:
            self.backend.activate_gremlin(True)
        if args.start_minimized:
            self.backend.minimize()

    def initialize_qt(self) -> None:
        QtCore.QLoggingCategory.setFilterRules(
            "qt.qml.binding.removal.info=true"
        )

        # Prevent blurry fonts that Qt seems to like
        # QtQuick.QQuickWindow.setTextRenderType(
        #     QtQuick.QQuickWindow.NativeTextRendering
        # )
        # Use software rendering to prevent flickering on variable refresh rate
        # displays.
        # QtQuick.QQuickWindow.setSceneGraphBackend("software")
        # QtQuick.QQuickWindow.setGraphicsApi(QtQuick.QSGRendererInterface.OpenGL)

        # Set application information.
        app_id = u"joystick.gremlin"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        self.setWindowIcon(
            QtGui.QIcon(gremlin.util.resource_path("gfx/icon.png"))
        )
        self.setApplicationDisplayName("Joystick Gremlin")
        self.setOrganizationName("H2IK")
        self.setOrganizationDomain(
            "https://whitemagic.github.io/JoystickGremlin/"
        )
        self.setApplicationName("Joystick Gremlin")

        # Change application wide font.
        self.setFont(QtGui.QFont("Segoe UI", 11))

        # Load font used for icons.
        if QtGui.QFontDatabase.addApplicationFont(":/BootstrapIcons") < 0:
            self.syslog.error("Failed to load BootstrapIcons")

        # Create application and UI engine.
        self.engine = QtQml.QQmlApplicationEngine(parent=self)
        self.engine.addImportPath(".")
        self.engine.addImportPath(str(Path(__file__).parent / "qml2"))

        QtQml.qmlRegisterSingletonType(
            QtCore.QUrl.fromLocalFile(
                str(Path(__file__).parent / "qml" / "Style.qml")
            ),
            "Gremlin.Style", 1, 0, "Style"
        )

        QtCore.QDir.addSearchPath(
            "core_plugins",
            gremlin.util.resource_path("action_plugins/")
        )
        QtCore.QDir.addSearchPath("qml", gremlin.util.resource_path("qml/"))

        self.cfg = Configuration()
        user_plugins_path = Path(self.cfg.value("global", "general", "plugin-directory"))
        if user_plugins_path.is_dir():
            QtCore.QDir.addSearchPath(
                "user_plugins",
                str(user_plugins_path)
            )

        # Create and register backend and signal objects
        self.backend = gremlin.ui.backend.Backend(self.engine)
        self.backend.newProfile()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.rootContext().setContextProperty(
            "uiState", self.backend.ui_state
        )
        self.engine.rootContext().setContextProperty(
            "signal", gremlin.signal.signal
        )


def main() -> int:
    # Create Joystick Gremlin instance and run it.
    app = JoystickGremlinApp(sys.argv)
    app.exec()
    logging.getLogger("system").info("Terminating Gremlin")

    return 0


if __name__ == "__main__":
    sys.exit(main())
