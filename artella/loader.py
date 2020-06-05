#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artella
"""

from __future__ import print_function, division, absolute_import

import os
import sys

import artella
from artella import dcc
from artella import logger


def init(init_client=True, plugin_paths=None, extensions=None):
    """
    Initializes Artella Plugin

    :param bool init_client: Whether or not Artella Drive Client should be initialized during initialization.
        Useful to avoid to connect to Artella client when developing DCC specific functionality.
    :return: True if Artella initialization was successful; False otherwise.
    :rtype: bool
    """

    from artella import register
    from artella.core import dcc as core_dcc
    from artella.core import client, resource, plugin, qtutils
    from artella.widgets import theme, color

    plugins_path = plugin_paths if plugin_paths is not None else list()
    extensions = extensions if extensions is not None else list()

    # Create logger
    logger.create_logger()

    # Make sure that Artella Drive client and DCC are cached during initialization
    core_dcc.current_dcc()

    # Specific DCC extensions are managed by the client
    dcc_extensions = dcc.extensions()
    extensions.extend(dcc_extensions)

    # Create Artella Drive Client
    artella_drive_client = client.ArtellaDriveClient.get(extensions=extensions) if init_client else None

    # Initialize resources
    resources_mgr = artella.ResourcesMgr()
    resources_mgr.register_resources_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'))

    # Load Plugins
    default_plugins_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
    if default_plugins_path not in plugins_path:
        plugins_path.append(default_plugins_path)
    artella.PluginsMgr().register_paths(plugins_path)
    artella.PluginsMgr().load_registered_plugins()

    # Initialize Artella DCC plugin
    artella.DccPlugin(artella_drive_client).init()

    if qtutils.QT_AVAILABLE:
        artella_theme = theme.ArtellaTheme(main_color=color.ArtellaColors.DEFAULT)
        register.register_class('theme', artella_theme)

    return True


def shutdown():
    """
    Shutdown Artella Plugin

    :return: True if Artella shutdown was successful; False otherwise.
    :rtype: bool
    """

    from artella.core import dcc
    from artella.core import plugin

    # Create logger
    logger.create_logger()

    # Make sure that Artella Drive client and DCC are cached during initialization
    dcc.current_dcc()

    artella.PluginsMgr().shutdown()
    artella.DccPlugin().shutdown()

    return True


def _reload():
    """
    Function to be used during development. Can be used to "reload" Artella modules.
    Useful when working inside DCC envs.
    """

    # Create logger
    logger.create_logger()

    # We make sure that plugin is shutdown before doing reload
    shutdown()

    to_clean = [m for m in sys.modules.keys() if 'artella' in m]
    for t in to_clean:
        del sys.modules[t]

    global CURRENT_DCC
    CURRENT_DCC = None
