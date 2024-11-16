# plugin_system.py

import os
import importlib.util

class PluginSystem:
    def __init__(self, gui):
        self.gui = gui
        self.plugins = []

    def load_plugins(self):
        plugins_dir = "plugins"
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
        for file in os.listdir(plugins_dir):
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(plugins_dir, file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.plugins.append(module)
                if hasattr(module, 'init'):
                    module.init(self.gui)