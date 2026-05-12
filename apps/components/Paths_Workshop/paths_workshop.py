#!/usr/bin/env python3
#this belongs in apps/components/Paths_Workshop/paths_workshop.py - Version: 1
# X-Seti - May12 2026 - Paths Workshop
"""
Paths Workshop — GTA SA/VC/III path node editor.
Base: RadarWorkshop. Adds path node overlay on radar map.
"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _root not in sys.path: sys.path.insert(0, _root)

from apps.components.Paths_Workshop.radar_workshop import RadarWorkshop

App_name   = "Paths Workshop"
App_build  = "Build 1"
config_key = "paths_workshop"


class PathsWorkshop(RadarWorkshop):
    App_name   = App_name
    App_build  = App_build
    config_key = config_key

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent, main_window)
        self._path_nodes = []
        self._path_links = []
    # TODO: _parse_nodes_dat, _draw_path_overlay, _on_node_click


def open_paths_workshop(main_window=None):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    w = PathsWorkshop(main_window=main_window)
    w.resize(1200, 800); w.show()
    return w
