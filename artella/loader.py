#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artella
"""

from __future__ import print_function, division, absolute_import

import os
import sys

import artella
from artella import logger
from artella.core import consts, utils


def init(init_client=True, plugin_paths=None, dcc_paths=None, extensions=None, dev=False):
    """
    Initializes Artella Plugin

    :param bool init_client: Whether or not Artella Drive Client should be initialized during initialization.
        Useful to avoid to connect to Artella client when developing DCC specific functionality.
    :return: True if Artella initialization was successful; False otherwise.
    :rtype: bool
    """

    plugins_path = plugin_paths if plugin_paths is not None else list()
    dccs_path = dcc_paths if dcc_paths is not None else list()
    extensions = extensions if extensions is not None else list()

    # Create logger
    logger.create_logger()

    # Register DCC paths
    valid_dcc_paths = list()
    default_dccs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dccs')
    if default_dccs_path not in dccs_path:
        dccs_path.append(default_dccs_path)
    for dcc_path in dccs_path:
        if os.path.isdir(dcc_path):
            if dcc_path not in sys.path:
                sys.path.append(dcc_path)
            valid_dcc_paths.append(dcc_path)
    if valid_dcc_paths:
        if os.environ.get(consts.AED, None):
            env = os.environ[consts.AED].split(';')
            env.extend(valid_dcc_paths)
            clean_env = list(set([utils.clean_path(pth) for pth in env]))
            dcc_paths_str = ';'.join(clean_env)
        else:
            dcc_paths_str = ';'.join(valid_dcc_paths)
        os.environ[consts.AED] = dcc_paths_str

    # Once DCC paths are registered we can import modules
    from artella import register
    from artella import dcc
    from artella.core import dcc as dcc_core
    from artella.core import client, resource, plugin, dccplugin, qtutils
    from artella.widgets import theme, color

    # Make sure that Artella Drive client and DCC are cached during initialization
    current_dcc = dcc_core.current_dcc()
    if not current_dcc:
        logger.log_error('Impossible to load Artella Plugin because no DCC is available!')
        return False

    # Specific DCC extensions are managed by the client
    dcc_extensions = dcc.extensions()
    extensions.extend(dcc_extensions)

    # Initialize resources and theme
    resources_mgr = artella.ResourcesMgr()
    resources_mgr.register_resources_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'))
    if qtutils.QT_AVAILABLE:
        artella_theme = theme.ArtellaTheme(main_color=color.ArtellaColors.DEFAULT)
        register.register_class('theme', artella_theme)

    # Create Artella Drive Client
    artella_drive_client = client.ArtellaDriveClient.get(extensions=extensions) if init_client else None

    # Load Plugins
    default_plugins_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
    if default_plugins_path not in plugins_path:
        plugins_path.append(default_plugins_path)
    artella.PluginsMgr().register_paths(plugins_path)
    artella.PluginsMgr().load_registered_plugins()

    # Initialize Artella DCC plugin
    artella.DccPlugin(artella_drive_client).init(dev=dev)

    return True


def shutdown():
    """
    Shutdown Artella Plugin

    :return: True if Artella shutdown was successful; False otherwise.
    :rtype: bool
    """

    # Create logger
    logger.create_logger()

    try:
        artella.PluginsMgr().shutdown()
        artella.DccPlugin().shutdown()
    except Exception as exc:
        pass

    clean_modules()

    return True


def clean_modules():
    """
    Clean all loaded modules related with artella from Python modules dictionary
    """

    to_clean = [m for m in sys.modules.keys() if m.startswith('artella.')]
    for t in to_clean:
        del sys.modules[t]


def _reload():
    """
    Function to be used during development. Can be used to "reload" Artella modules.
    Useful when working inside DCC envs.
    """

    # Create logger
    logger.create_logger()

    # We make sure that plugin is shutdown before doing reload
    shutdown()

    global CURRENT_DCC
    CURRENT_DCC = None
