#!/usr/bin/env python3
#this belongs in root /launch_paths_workshop.py - Version: 2
# X-Seti - October 19 2026 - Paths-Workshop launcher
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apps.components.Path_Workshop.path_workshop import open_path_workshop
from PyQt6.QtWidgets import QApplication
if __name__ == '__main__':
    try:
        from PyQt6.QtGui import QSurfaceFormat
        f=QSurfaceFormat(); f.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
        f.setVersion(2,1); QSurfaceFormat.setDefaultFormat(f)
    except Exception: pass
    app = QApplication(sys.argv)
    w = open_path_workshop()
    sys.exit(app.exec())
