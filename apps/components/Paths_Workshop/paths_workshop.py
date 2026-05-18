#!/usr/bin/env python3
#this belongs in apps/components/Paths_Workshop/paths_workshop.py - Version: 2
# X-Seti - May18 2026 - Paths Workshop
"""
Paths Workshop - GTA III/VC/SA path node editor.
Base: RadarWorkshop radar map canvas as background.

##Methods list -
# PathNode.__init__
# NodeParser.__init__
# NodeParser.load
# NodeParser.load_gta3_vc
# NodeParser.load_sa
# NodeParser.save
# NodeParser.save_gta3_vc
# NodeParser.save_sa
# NodeMapCanvas.__init__
# NodeMapCanvas.set_nodes
# NodeMapCanvas.set_radar
# NodeMapCanvas.fit_all
# NodeMapCanvas._world_to_screen
# NodeMapCanvas._screen_to_world
# NodeMapCanvas._hit_test
# NodeMapCanvas._node_visible
# NodeMapCanvas._node_colour
# NodeMapCanvas.paintEvent
# NodeMapCanvas.mousePressEvent
# NodeMapCanvas.mouseMoveEvent
# NodeMapCanvas.mouseReleaseEvent
# NodeMapCanvas.wheelEvent
# NodeMapCanvas.contextMenuEvent
# NodesTab.__init__
# NodesTab._build_ui
# NodesTab.load_file
# NodesTab.save_file
# NodesTab.set_radar
# NodesTab._refresh_list
# NodesTab._filter_changed
# NodesTab._on_node_selected
# NodesTab._on_field_changed
# NodesTab._on_map_click
# NodesTab._on_map_move
# NodesTab._add_node
# NodesTab._delete_node
# PathsWorkshop.__init__
# PathsWorkshop._ensure_path_tabs
# PathsWorkshop._make_text_tab
# PathsWorkshop._detect_game
# PathsWorkshop._open_path_file
# PathsWorkshop._load_radar_image
# PathsWorkshop._build_menus_into_qmenu
# open_paths_workshop
"""

import sys, os, math, struct
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _root not in sys.path: sys.path.insert(0, _root)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QTabWidget, QDoubleSpinBox, QSpinBox,
    QPushButton, QFileDialog, QMessageBox, QApplication, QFormLayout,
    QGroupBox, QCheckBox, QComboBox, QMenu, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QImage, QPolygonF

from apps.components.Paths_Workshop.radar_workshop import RadarWorkshop

App_name   = "Paths Workshop"
App_build  = "Build 2"
config_key = "paths_workshop"


# ─────────────────────────────────────────────────────────────────────────────
# Data class
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PathNode:  #vers 1
    idx:     int   = 0
    x:       float = 0.0
    y:       float = 0.0
    z:       float = 0.0
    flags:   int   = 1      # bit0=car, bit1=ped, bit2=boat, bit3=disabled
    links:   List[int] = field(default_factory=list)
    area_id: int   = 0
    node_id: int   = 0

    @property
    def is_car(self):   return bool(self.flags & 1)
    @property
    def is_ped(self):   return bool(self.flags & 2)
    @property
    def is_boat(self):  return bool(self.flags & 4)
    @property
    def disabled(self): return bool(self.flags & 8)

    def type_str(self):
        t = []
        if self.is_car:  t.append("Car")
        if self.is_ped:  t.append("Ped")
        if self.is_boat: t.append("Boat")
        return "/".join(t) or "?"


# ─────────────────────────────────────────────────────────────────────────────
# Node parser  (GTA3 / VC / SA)
# ─────────────────────────────────────────────────────────────────────────────

class NodeParser:  #vers 1
    """Binary nodes.dat parser for GTA3, VC and SA."""

    GTA3_NODE_SIZE = 20   # x,y,z float32 + unk1 uint32 + unk2 uint16 + flags uint8 + link_count uint8
    SA_NODE_SIZE   = 28   # compressed int16 coords + extra fields

    def __init__(self):  #vers 1
        self.nodes:    List[PathNode] = []
        self.game:     str = "gta3"
        self.filename: str = ""

    def load(self, path: str, game: str = None) -> bool:  #vers 1
        self.filename = os.path.basename(path)
        stem = os.path.splitext(self.filename.lower())[0]
        if game:
            self.game = game.lower()
        elif stem == "nodes":
            self.game = "gta3"   # nodes.dat = GTA3 or VC (same format)
        elif stem.startswith("nodes") and stem != "nodes":
            self.game = "sa"     # nodes0.dat..nodes8.dat = SA
        else:
            self.game = "gta3"
        return self.load_sa(path) if self.game == "sa" else self.load_gta3_vc(path)

    def load_gta3_vc(self, path: str) -> bool:  #vers 1
        """GTA3 / VC nodes.dat:
        Header: uint32 node_count
        Nodes:  x,y,z float32 | unk1 uint32 | unk2 uint16 | flags uint8 | link_count uint8
        Links:  uint32[] after all nodes"""
        try:
            self.nodes.clear()
            data = open(path, "rb").read()
            if len(data) < 4: return False
            pos = 0
            n_nodes = struct.unpack_from("<I", data, pos)[0]; pos += 4
            if len(data) < 4 + n_nodes * self.GTA3_NODE_SIZE:
                print(f"[NodeParser] file too small for {n_nodes} nodes"); return False
            link_counts = []
            for i in range(n_nodes):
                x, y, z = struct.unpack_from("<fff", data, pos); pos += 12
                pos += 4   # unk1
                pos += 2   # unk2
                flags  = struct.unpack_from("<B", data, pos)[0]; pos += 1
                lcount = struct.unpack_from("<B", data, pos)[0]; pos += 1
                self.nodes.append(PathNode(idx=i, x=x, y=y, z=z, flags=flags))
                link_counts.append(lcount)
            for i, lcount in enumerate(link_counts):
                for _ in range(lcount):
                    if pos + 4 <= len(data):
                        tgt = struct.unpack_from("<I", data, pos)[0]; pos += 4
                        self.nodes[i].links.append(tgt)
            print(f"[NodeParser] GTA3/VC: {len(self.nodes)} nodes from {self.filename}")
            return True
        except Exception as ex:
            print(f"NodeParser.load_gta3_vc: {ex}"); return False

    def load_sa(self, path: str) -> bool:  #vers 1
        """SA nodes0-8.dat NaviNode format:
        Header: uint32 node_count
        Nodes:  x,y,z int16 (*8 = world coord) | area_id uint16 | node_id uint32
                unk1 uint8 | unk2 uint8 | link_id uint16 | path_width uint8
                node_type uint8 | flags uint16 | link_count uint8 | unk3 uint8"""
        try:
            self.nodes.clear()
            data = open(path, "rb").read()
            if len(data) < 4: return False
            pos = 0
            n_nodes = struct.unpack_from("<I", data, pos)[0]; pos += 4
            for i in range(n_nodes):
                if pos + self.SA_NODE_SIZE > len(data): break
                mx = struct.unpack_from("<h", data, pos)[0]; pos += 2
                my = struct.unpack_from("<h", data, pos)[0]; pos += 2
                mz = struct.unpack_from("<h", data, pos)[0]; pos += 2
                area_id = struct.unpack_from("<H", data, pos)[0]; pos += 2
                node_id = struct.unpack_from("<I", data, pos)[0]; pos += 4
                pos += 2   # unk1, unk2
                pos += 2   # link_id
                pos += 1   # path_width
                node_type = struct.unpack_from("<B", data, pos)[0]; pos += 1
                pos += 2   # flags
                link_count = struct.unpack_from("<B", data, pos)[0]; pos += 1
                pos += 1   # unk3
                x = mx / 8.0; y = my / 8.0; z = mz / 8.0
                flags = {0: 1, 1: 2, 4: 4}.get(node_type, 1)
                node = PathNode(idx=i, x=x, y=y, z=z, flags=flags,
                                area_id=area_id, node_id=node_id)
                self.nodes.append(node)
            print(f"[NodeParser] SA: {len(self.nodes)} nodes from {self.filename}")
            return True
        except Exception as ex:
            print(f"NodeParser.load_sa: {ex}"); return False

    def save(self, path: str) -> bool:  #vers 1
        return self.save_sa(path) if self.game == "sa" else self.save_gta3_vc(path)

    def save_gta3_vc(self, path: str) -> bool:  #vers 1
        try:
            with open(path, "wb") as f:
                f.write(struct.pack("<I", len(self.nodes)))
                for node in self.nodes:
                    f.write(struct.pack("<fff", node.x, node.y, node.z))
                    f.write(struct.pack("<IH", 0, 0))
                    f.write(struct.pack("<BB", node.flags & 0xFF, len(node.links)))
                for node in self.nodes:
                    for tgt in node.links:
                        f.write(struct.pack("<I", tgt))
            return True
        except Exception as ex:
            print(f"NodeParser.save_gta3_vc: {ex}"); return False

    def save_sa(self, path: str) -> bool:  #vers 1
        try:
            with open(path, "wb") as f:
                f.write(struct.pack("<I", len(self.nodes)))
                for node in self.nodes:
                    mx = max(-32768, min(32767, int(node.x * 8)))
                    my = max(-32768, min(32767, int(node.y * 8)))
                    mz = max(-32768, min(32767, int(node.z * 8)))
                    nt = 0 if node.is_car else (1 if node.is_ped else 4)
                    f.write(struct.pack("<hhhH", mx, my, mz, node.area_id))
                    f.write(struct.pack("<I",  node.node_id))
                    f.write(b"\x00\x00")
                    f.write(struct.pack("<H", 0))
                    f.write(struct.pack("<BB", 4, nt))
                    f.write(struct.pack("<HBB", 0, len(node.links), 0))
                f.write(struct.pack("<I", 0))
            return True
        except Exception as ex:
            print(f"NodeParser.save_sa: {ex}"); return False


# ─────────────────────────────────────────────────────────────────────────────
# Node map canvas
# ─────────────────────────────────────────────────────────────────────────────

class NodeMapCanvas(QWidget):  #vers 1
    node_clicked = pyqtSignal(int)
    node_moved   = pyqtSignal(int, float, float)

    SHOW_CAR  = 1
    SHOW_PED  = 2
    SHOW_BOAT = 4

    WORLD_MIN = -3000.0
    WORLD_MAX =  3000.0
    R_NODE = 4;  R_SEL = 8
    C_CAR  = QColor(80, 220, 120)
    C_PED  = QColor(100, 160, 255)
    C_BOAT = QColor(80, 200, 230)
    C_SEL  = QColor(255, 220, 50)
    C_DIS  = QColor(100, 100, 100)
    C_LINK = QColor(255, 255, 255, 55)

    def __init__(self, parent=None):  #vers 1
        super().__init__(parent)
        self._nodes: List[PathNode] = []
        self._radar: Optional[QImage] = None
        self._sel_idx  = -1
        self._drag_idx = -1
        self._pan_x = 0.0; self._pan_y = 0.0; self._zoom = 0.1
        self._last_pan = None
        self._show_links  = True
        self._show_labels = False
        self._show_filter = self.SHOW_CAR | self.SHOW_PED | self.SHOW_BOAT
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

    def set_nodes(self, nodes: List[PathNode]):  #vers 1
        self._nodes = nodes; self._sel_idx = -1; self.fit_all(); self.update()

    def set_radar(self, img: QImage):  #vers 1
        self._radar = img; self.update()

    def set_filter(self, mask: int):  #vers 1
        self._show_filter = mask; self.update()

    def fit_all(self):  #vers 1
        if not self._nodes: return
        xs = [n.x for n in self._nodes]; ys = [n.y for n in self._nodes]
        mx1,mx2 = min(xs)-200, max(xs)+200; my1,my2 = min(ys)-200, max(ys)+200
        W,H = max(self.width(),400), max(self.height(),400)
        sx,sy = mx2-mx1, my2-my1
        if sx<=0 or sy<=0: return
        self._zoom = min(W/sx, H/sy)
        cx,cy = (mx1+mx2)/2, (my1+my2)/2
        self._pan_x = W/2 - cx*self._zoom
        self._pan_y = H/2 + cy*self._zoom
        self.update()

    def _world_to_screen(self, wx, wy):  #vers 1
        return QPointF(wx*self._zoom + self._pan_x, -wy*self._zoom + self._pan_y)

    def _screen_to_world(self, sx, sy):  #vers 1
        return (sx-self._pan_x)/self._zoom, -(sy-self._pan_y)/self._zoom

    def _hit_test(self, sx, sy):  #vers 1
        r2 = (self.R_NODE+6)**2
        best=-1; bd=r2
        for i,n in enumerate(self._nodes):
            if not self._node_visible(n): continue
            pt = self._world_to_screen(n.x, n.y)
            d = (pt.x()-sx)**2+(pt.y()-sy)**2
            if d<bd: bd=d; best=i
        return best

    def _node_visible(self, n: PathNode):  #vers 1
        if n.is_car  and (self._show_filter & self.SHOW_CAR):  return True
        if n.is_ped  and (self._show_filter & self.SHOW_PED):  return True
        if n.is_boat and (self._show_filter & self.SHOW_BOAT): return True
        return False

    def _node_colour(self, n: PathNode):  #vers 1
        if n.disabled: return self.C_DIS
        if n.is_ped:   return self.C_PED
        if n.is_boat:  return self.C_BOAT
        return self.C_CAR

    def paintEvent(self, event):  #vers 1
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W,H = self.width(), self.height()

        if self._radar:
            tl = self._world_to_screen(self.WORLD_MIN, self.WORLD_MAX)
            br = self._world_to_screen(self.WORLD_MAX, self.WORLD_MIN)
            p.drawImage(QRectF(tl,br), self._radar,
                        QRectF(0,0,self._radar.width(),self._radar.height()))
        else:
            p.fillRect(self.rect(), QColor(20,26,36))
            p.setPen(QPen(QColor(38,52,68),1))
            for x in range(int(self.WORLD_MIN),int(self.WORLD_MAX)+1,500):
                p.drawLine(self._world_to_screen(x,self.WORLD_MIN),
                           self._world_to_screen(x,self.WORLD_MAX))
            for y in range(int(self.WORLD_MIN),int(self.WORLD_MAX)+1,500):
                p.drawLine(self._world_to_screen(self.WORLD_MIN,y),
                           self._world_to_screen(self.WORLD_MAX,y))

        if not self._nodes:
            p.setPen(QColor(150,160,190)); p.setFont(QFont("Arial",13))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No nodes loaded\n\nFile > Open nodes.dat")
            return

        # Links for selected node
        if self._show_links and 0 <= self._sel_idx < len(self._nodes):
            sn = self._nodes[self._sel_idx]
            p.setPen(QPen(self.C_LINK,1))
            pt1 = self._world_to_screen(sn.x, sn.y)
            for tgt in sn.links:
                if 0<=tgt<len(self._nodes):
                    tn = self._nodes[tgt]
                    pt2 = self._world_to_screen(tn.x, tn.y)
                    p.drawLine(pt1, pt2)
                    dx=pt2.x()-pt1.x(); dy=pt2.y()-pt1.y()
                    ln=math.sqrt(dx*dx+dy*dy)
                    if ln>12:
                        dx/=ln; dy/=ln
                        mx=(pt1.x()+pt2.x())/2; my=(pt1.y()+pt2.y())/2
                        p.setBrush(QBrush(self.C_LINK))
                        p.drawPolygon(QPolygonF([
                            QPointF(mx+dx*6,my+dy*6),
                            QPointF(mx-dy*3,my+dx*3),
                            QPointF(mx+dy*3,my-dx*3)]))
                        p.setBrush(Qt.BrushStyle.NoBrush)

        # Nodes
        p.setFont(QFont("Arial",7))
        for i,n in enumerate(self._nodes):
            if not self._node_visible(n): continue
            pt = self._world_to_screen(n.x, n.y)
            if pt.x()<-10 or pt.x()>W+10 or pt.y()<-10 or pt.y()>H+10: continue
            r = self.R_SEL if i==self._sel_idx else self.R_NODE
            col = self.C_SEL if i==self._sel_idx else self._node_colour(n)
            p.setPen(QPen(QColor(0,0,0,80),1)); p.setBrush(QBrush(col))
            p.drawEllipse(pt, r, r)
            if self._show_labels:
                p.setPen(QColor(210,215,240))
                p.drawText(int(pt.x())+r+2, int(pt.y())+4, str(i))

        visible = sum(1 for n in self._nodes if self._node_visible(n))
        p.setPen(QColor(170,180,210)); p.setFont(QFont("Arial",8))
        p.drawText(6,16, f"{len(self._nodes)} nodes  ({visible} visible)  zoom:{self._zoom:.3f}x")
        if 0<=self._sel_idx<len(self._nodes):
            n=self._nodes[self._sel_idx]
            p.drawText(6,H-6,
                f"[{n.idx}] {n.type_str()}  X:{n.x:.1f}  Y:{n.y:.1f}  Z:{n.z:.1f}  links:{len(n.links)}")

    def mousePressEvent(self, event):  #vers 1
        pos = event.position()
        if event.button()==Qt.MouseButton.LeftButton:
            idx = self._hit_test(pos.x(), pos.y())
            self._sel_idx=idx; self._drag_idx=idx
            if idx>=0: self.node_clicked.emit(idx)
            self.update()
        elif event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._last_pan = pos

    def mouseMoveEvent(self, event):  #vers 1
        pos = event.position()
        if (event.buttons() & (Qt.MouseButton.MiddleButton|Qt.MouseButton.RightButton)) and self._last_pan:
            dx=pos.x()-self._last_pan.x(); dy=pos.y()-self._last_pan.y()
            self._pan_x+=dx; self._pan_y+=dy; self._last_pan=pos; self.update()
        elif event.buttons()&Qt.MouseButton.LeftButton and self._drag_idx>=0:
            wx,wy=self._screen_to_world(pos.x(),pos.y())
            self._nodes[self._drag_idx].x=wx; self._nodes[self._drag_idx].y=wy
            self.node_moved.emit(self._drag_idx,wx,wy); self.update()

    def mouseReleaseEvent(self, event):  #vers 1
        self._drag_idx=-1; self._last_pan=None

    def wheelEvent(self, event):  #vers 1
        f=1.18 if event.angleDelta().y()>0 else 1.0/1.18
        pos=event.position()
        wx,wy=self._screen_to_world(pos.x(),pos.y())
        self._zoom=max(0.01,min(self._zoom*f,200.0))
        self._pan_x=pos.x()-wx*self._zoom
        self._pan_y=pos.y()+wy*self._zoom
        self.update()

    def contextMenuEvent(self, event):  #vers 1
        pos=event.pos(); wx,wy=self._screen_to_world(pos.x(),pos.y())
        m=QMenu(self)
        m.addAction("Add Car node here",  lambda:self._req_add(wx,wy,0))
        m.addAction("Add Ped node here",  lambda:self._req_add(wx,wy,1))
        m.addAction("Add Boat node here", lambda:self._req_add(wx,wy,2))
        if self._sel_idx>=0:
            m.addSeparator()
            m.addAction("Delete selected", lambda:self.node_clicked.emit(-9999))
        m.exec(event.globalPos())

    def _req_add(self, x, y, ntype):  #vers 1
        self._pending_add=(x,y,ntype); self.node_clicked.emit(-9998)


# ─────────────────────────────────────────────────────────────────────────────
# Nodes Tab
# ─────────────────────────────────────────────────────────────────────────────

class NodesTab(QWidget):  #vers 1
    def __init__(self, parent=None):  #vers 1
        super().__init__(parent)
        self._parser=NodeParser(); self._path=None; self._cur_idx=-1; self._blocking=False
        self._build_ui()

    def _build_ui(self):  #vers 1
        root=QHBoxLayout(self); root.setContentsMargins(4,4,4,4)
        sp=QSplitter(Qt.Orientation.Horizontal)

        left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(4,4,4,4); ll.setSpacing(4)

        # Filter
        fr=QHBoxLayout()
        self._cb_car=QCheckBox("Car"); self._cb_car.setChecked(True)
        self._cb_ped=QCheckBox("Ped"); self._cb_ped.setChecked(True)
        self._cb_boat=QCheckBox("Boat"); self._cb_boat.setChecked(True)
        for cb in (self._cb_car,self._cb_ped,self._cb_boat):
            cb.stateChanged.connect(self._filter_changed); fr.addWidget(cb)
        fr.addStretch(); ll.addLayout(fr)

        self._search=QLineEdit(); self._search.setPlaceholderText("Search…")
        self._search.textChanged.connect(self._filter_changed); ll.addWidget(self._search)

        self._list=QListWidget(); self._list.setFont(QFont("Monospace",8))
        self._list.currentRowChanged.connect(self._on_node_selected)
        ll.addWidget(self._list,1)

        grp=QGroupBox("Selected Node"); fl=QFormLayout(grp); fl.setSpacing(3)
        self._fx=QDoubleSpinBox(); self._fx.setRange(-10000,10000); self._fx.setDecimals(2)
        self._fy=QDoubleSpinBox(); self._fy.setRange(-10000,10000); self._fy.setDecimals(2)
        self._fz=QDoubleSpinBox(); self._fz.setRange(-1000,1000);   self._fz.setDecimals(2)
        self._ftype=QComboBox(); self._ftype.addItems(["Car","Ped","Boat"])
        self._fdis=QCheckBox("Disabled")
        self._flabel=QLabel("—")
        for lbl,w in (("X",self._fx),("Y",self._fy),("Z",self._fz),
                      ("Type",self._ftype),("",self._fdis),("Links",self._flabel)):
            fl.addRow(lbl,w)
        for w in (self._fx,self._fy,self._fz):
            w.valueChanged.connect(self._on_field_changed)
        self._ftype.currentIndexChanged.connect(self._on_field_changed)
        self._fdis.stateChanged.connect(self._on_field_changed)
        ll.addWidget(grp)

        br=QHBoxLayout()
        for lbl,fn in (("+Car",lambda:self._add_node(0)),("+Ped",lambda:self._add_node(1)),
                       ("Del",self._delete_node)):
            b=QPushButton(lbl); b.setFixedHeight(24); b.clicked.connect(fn); br.addWidget(b)
        ll.addLayout(br)

        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(0,0,0,0)
        tb=QHBoxLayout()
        fit=QPushButton("Fit [F]"); fit.setFixedHeight(24); fit.clicked.connect(lambda:self._map.fit_all())
        lk=QCheckBox("Links"); lk.setChecked(True)
        lk.stateChanged.connect(lambda v:setattr(self._map,"_show_links",bool(v)) or self._map.update())
        lb=QCheckBox("Labels"); lb.setChecked(False)
        lb.stateChanged.connect(lambda v:setattr(self._map,"_show_labels",bool(v)) or self._map.update())
        self._status=QLabel("No file")
        self._status.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        for w in (fit,lk,lb,self._status): tb.addWidget(w)
        self._map=NodeMapCanvas()
        self._map.node_clicked.connect(self._on_map_click)
        self._map.node_moved.connect(self._on_map_move)
        rl.addLayout(tb); rl.addWidget(self._map,1)

        sp.addWidget(left); sp.addWidget(right); sp.setSizes([280,800]); root.addWidget(sp)

    def load_file(self, path: str, game: str=None) -> bool:  #vers 1
        ok=self._parser.load(path,game)
        if ok:
            self._path=path; self._refresh_list()
            self._map.set_nodes(self._parser.nodes)
            self._status.setText(
                f"{os.path.basename(path)}  —  {len(self._parser.nodes)} nodes  ({self._parser.game.upper()})")
        return ok

    def save_file(self, path: str) -> bool:  #vers 1
        return self._parser.save(path)

    def set_radar(self, img: QImage):  #vers 1
        self._map.set_radar(img)

    @property
    def current_path(self): return self._path

    def _refresh_list(self):  #vers 1
        self._list.clear()
        query=self._search.text().lower()
        mask=0
        if self._cb_car.isChecked():  mask|=NodeMapCanvas.SHOW_CAR
        if self._cb_ped.isChecked():  mask|=NodeMapCanvas.SHOW_PED
        if self._cb_boat.isChecked(): mask|=NodeMapCanvas.SHOW_BOAT
        self._map.set_filter(mask)
        for n in self._parser.nodes:
            if not self._map._node_visible(n): continue
            if query and query not in str(n.idx) and query not in n.type_str().lower(): continue
            item=QListWidgetItem(
                f"[{n.idx:5d}] {n.type_str():5s} {n.x:8.1f} {n.y:8.1f} {n.z:6.1f}  lnk:{len(n.links)}")
            item.setData(Qt.ItemDataRole.UserRole,n.idx)
            self._list.addItem(item)

    def _filter_changed(self):  #vers 1
        self._refresh_list()

    def _on_node_selected(self, row: int):  #vers 1
        item=self._list.item(row)
        if not item: return
        idx=item.data(Qt.ItemDataRole.UserRole)
        if idx is None or idx>=len(self._parser.nodes): return
        self._cur_idx=idx; n=self._parser.nodes[idx]
        self._blocking=True
        self._fx.setValue(n.x); self._fy.setValue(n.y); self._fz.setValue(n.z)
        self._ftype.setCurrentIndex(1 if n.is_ped else (2 if n.is_boat else 0))
        self._fdis.setChecked(n.disabled)
        self._flabel.setText(f"{len(n.links)} → {n.links[:5]}" + ("…" if len(n.links)>5 else ""))
        self._blocking=False
        self._map._sel_idx=idx; self._map.update()

    def _on_field_changed(self):  #vers 1
        if self._blocking or self._cur_idx<0 or self._cur_idx>=len(self._parser.nodes): return
        n=self._parser.nodes[self._cur_idx]
        n.x=self._fx.value(); n.y=self._fy.value(); n.z=self._fz.value()
        nt=self._ftype.currentIndex()
        n.flags=(1 if nt==0 else (2 if nt==1 else 4))|(8 if self._fdis.isChecked() else 0)
        self._map.update()

    def _on_map_click(self, idx: int):  #vers 1
        if idx==-9998:
            p=getattr(self._map,"_pending_add",None)
            if p: self._add_node(p[2],p[0],p[1]); return
        if idx==-9999:
            self._delete_node(); return
        if idx<0: return
        for row in range(self._list.count()):
            item=self._list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole)==idx:
                self._list.setCurrentRow(row); break

    def _on_map_move(self, idx: int, x: float, y: float):  #vers 1
        if idx!=self._cur_idx: return
        self._blocking=True; self._fx.setValue(x); self._fy.setValue(y); self._blocking=False

    def _add_node(self, ntype: int=0, x: float=0.0, y: float=0.0):  #vers 1
        flags=1 if ntype==0 else (2 if ntype==1 else 4)
        n=PathNode(idx=len(self._parser.nodes),x=x,y=y,z=0.0,flags=flags)
        self._parser.nodes.append(n); self._refresh_list()
        self._map.set_nodes(self._parser.nodes)
        self._list.setCurrentRow(self._list.count()-1)

    def _delete_node(self):  #vers 1
        if self._cur_idx<0: return
        self._parser.nodes.pop(self._cur_idx)
        for i,n in enumerate(self._parser.nodes): n.idx=i
        self._cur_idx=-1; self._refresh_list(); self._map.set_nodes(self._parser.nodes)


# ─────────────────────────────────────────────────────────────────────────────
# PathsWorkshop — inherits RadarWorkshop
# ─────────────────────────────────────────────────────────────────────────────

class PathsWorkshop(RadarWorkshop):  #vers 2
    App_name   = App_name
    App_build  = App_build
    config_key = config_key

    _ROUTES = {
        "nodes":   (0,"gta3"),
        "nodes0":  (0,"sa"), "nodes1":(0,"sa"), "nodes2":(0,"sa"), "nodes3":(0,"sa"),
        "nodes4":  (0,"sa"), "nodes5":(0,"sa"), "nodes6":(0,"sa"), "nodes7":(0,"sa"),
        "nodes8":  (0,"sa"),
        "train":   (1,None), "train2": (1,None),
        "flight":  (2,None), "flight2":(2,None), "flight3":(2,None),
        "spath0":  (3,None),
    }

    def __init__(self, parent=None, main_window=None):  #vers 2
        super().__init__(parent, main_window)
        self._radar_image: Optional[QImage] = None
        self._path_tabs_built = False
        self._ensure_path_tabs()

    def _ensure_path_tabs(self):  #vers 1
        if self._path_tabs_built: return
        if hasattr(self,"_main_tabs"):
            tw=self._main_tabs
        else:
            tw=QTabWidget()
            if hasattr(self,"centre_layout"):
                self.centre_layout.addWidget(tw)
            self._main_tabs=tw
        self._tab_nodes  = NodesTab()
        self._tab_train  = self._make_text_tab("train")
        self._tab_flight = self._make_text_tab("flight")
        self._tab_spath  = self._make_text_tab("spath")
        tw.addTab(self._tab_nodes,  "Nodes")
        tw.addTab(self._tab_train,  "Train")
        tw.addTab(self._tab_flight, "Flight")
        tw.addTab(self._tab_spath,  "Static Paths")
        self._path_tabs_built=True

    def _make_text_tab(self, kind: str) -> QWidget:  #vers 1
        try:
            base=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Path_Workshop")
            if base not in sys.path: sys.path.insert(0,base)
            from path_workshop import TrainTab, FlightTab, SpathTab
            if kind=="train":  return TrainTab()
            if kind=="flight": return FlightTab()
            if kind=="spath":  return SpathTab()
        except ImportError:
            pass
        w=QWidget(); l=QVBoxLayout(w)
        l.addWidget(QLabel(f"{kind} editor — open a .dat file")); return w

    def _detect_game(self, path: str) -> str:  #vers 1
        stem=os.path.splitext(os.path.basename(path).lower())[0]
        if stem=="nodes": return "gta3"
        if stem.startswith("nodes") and stem!="nodes": return "sa"
        return "gta3"

    def _open_path_file(self, path: str=None):  #vers 1
        if path is None:
            path,_=QFileDialog.getOpenFileName(self,"Open Path File","",
                "Path files (nodes*.dat train*.dat flight*.dat spath0.dat *.dat);;All files (*)")
        if not path: return
        stem=os.path.splitext(os.path.basename(path).lower())[0]
        tab_idx,game=self._ROUTES.get(stem,(0,None))
        if game is None: game=self._detect_game(path)
        tabs=[self._tab_nodes,self._tab_train,self._tab_flight,self._tab_spath]
        tab=tabs[tab_idx]
        ok=tab.load_file(path,game) if tab_idx==0 else (tab.load_file(path) if hasattr(tab,"load_file") else False)
        if ok:
            if self._radar_image and hasattr(tab,"set_radar"): tab.set_radar(self._radar_image)
            self._main_tabs.setCurrentIndex(tab_idx)
            self._set_status(f"Loaded: {os.path.basename(path)}")
        else:
            QMessageBox.critical(self,"Error",f"Failed to load {os.path.basename(path)}")

    def _load_radar_image(self, path: str=None):  #vers 1
        if path is None:
            path,_=QFileDialog.getOpenFileName(self,"Load Radar Image","",
                "Images (*.png *.jpg *.bmp);;All files (*)")
        if not path: return
        img=QImage(path)
        if img.isNull():
            QMessageBox.warning(self,"Radar",f"Could not load {path}"); return
        self._radar_image=img
        for tab in (self._tab_nodes,self._tab_train,self._tab_flight,self._tab_spath):
            if hasattr(tab,"set_radar"): tab.set_radar(img)
        self._set_status(f"Radar: {os.path.basename(path)}")

    def _build_menus_into_qmenu(self, pm):  #vers 1
        fm=pm.addMenu("File")
        fm.addAction("Open Path File…", self._open_path_file)
        fm.addAction("Load Radar Image…", self._load_radar_image)
        fm.addSeparator()
        fm.addAction("Open nodes.dat (GTA3/VC)", lambda:self._open_specific("gta3"))
        fm.addAction("Open nodes0-8.dat (SA)",   lambda:self._open_specific("sa"))
        fm.addAction("Open train.dat",  lambda:self._open_specific("train"))
        fm.addAction("Open flight.dat", lambda:self._open_specific("flight"))
        fm.addSeparator()
        fm.addAction("Close", self.close)

    def _open_specific(self, kind: str):  #vers 1
        filters={
            "gta3": "nodes.dat (nodes.dat *.dat)",
            "sa":   "SA nodes (nodes0.dat nodes1.dat nodes2.dat *.dat)",
            "train":"train.dat (train.dat train2.dat *.dat)",
            "flight":"flight.dat (flight*.dat *.dat)",
        }
        path,_=QFileDialog.getOpenFileName(self,f"Open {kind} path","",
            filters.get(kind,"DAT files (*.dat)"))
        if path: self._open_path_file(path)


def open_paths_workshop(main_window=None, path: str=None):  #vers 1
    from PyQt6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication(sys.argv)
    w=PathsWorkshop(main_window=main_window)
    w.resize(1280,860); w.show()
    if path: w._open_path_file(path)
    return w
