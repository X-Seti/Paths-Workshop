#!/usr/bin/env python3
#this belongs in paths_workshop.py - Version: 1
# X-Seti - May12 2026 - Paths Workshop
"""
Paths Workshop — GTA SA/VC/III path node editor.
Base: RadarWorkshop (radar map display + tile viewer).
Adds: path node overlay on radar map, node editing, path export.

Supported files:
  data/paths/  — SA path node files
  nodes0..nodes12.dat — SA/VC path data
"""

import sys, os
from pathlib import Path

_depends = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'depends')
if _depends not in sys.path:
    sys.path.insert(0, _depends)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from radar_workshop import RadarWorkshop, RADSettings

App_name   = "Paths Workshop"
App_build  = "Build 1"
App_auth   = "X-Seti"
config_key = "paths_workshop"


class PathsWorkshop(RadarWorkshop):
    """Path node editor — extends RadarWorkshop with path overlay."""

    App_name   = App_name
    App_build  = App_build
    config_key = config_key

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent, main_window)
        self._path_nodes  = []   # list of (x, y, z, type, flags)
        self._path_links  = []   # list of (node_a, node_b)

    # TODO: _parse_nodes_dat(path)   — parse SA nodesX.dat format
    # TODO: _draw_path_overlay()     — draw nodes/links on radar grid (QPainter)
    # TODO: _on_node_click(x, y)     — select/edit node at radar position
    # TODO: _export_nodes_dat(path)  — write back to binary format


def open_paths_workshop(main_window=None):
    app = QApplication.instance() or QApplication(sys.argv)
    w = PathsWorkshop(main_window=main_window)
    w.resize(1200, 800)
    w.show()
    return w


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = PathsWorkshop()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())
