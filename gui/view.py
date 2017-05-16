import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class View(QGraphicsView):
	def __init__(self, *args):
		super().__init__(*args)
		self.center()
		self.scene().new_circuit.connect(self.center)
		self.setRenderHint(QPainter.Antialiasing)
		self.setAcceptDrops(True)

		self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setDragMode(QGraphicsView.ScrollHandDrag)
		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

	def setScene(self, scene):
		super().setScene(scene)
		self.scene().new_circuit.connect(self.center)

	def center(self):
		self.centerOn(self.scene().itemsBoundingRect().center())

	def fit_to_scene(self):
		self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

	def wheelEvent(self, e):
		degrees = e.angleDelta().y() / 8.
		steps = degrees / 15.
		scale = 1.1 ** steps
		self.scale(scale, scale)
		e.accept()

	def enterEvent(self, *args):
		super().enterEvent(*args)
		self.viewport().unsetCursor()

	def mousePressEvent(self, *args):
		super().mousePressEvent(*args)
		self.viewport().unsetCursor()

	def mouseReleaseEvent(self, *args):
		super().mouseReleaseEvent(*args)
		self.viewport().unsetCursor()

	def mouseMoveEvent(self, e):
		super().mouseMoveEvent(e)
		if e.buttons() == Qt.LeftButton:
			self.viewport().setCursor(Qt.ClosedHandCursor)
		else:
			self.viewport().unsetCursor()
			if self.scene().partial_wire is not None:
				self.scene().partial_wire.update_path(self.mapToScene(e.pos()))
		e.accept()

	def dragEnterEvent(self, e):
		if e.mimeData().hasFormat('application/gate-type'):
			gate_type = pickle.loads(e.mimeData().data('application/gate-type'))
			self.scene().build_gate(self.mapToScene(e.pos()), gate_type)
			e.accept()
		else:
			return super().dragEnterEvent(e)

	def dragMoveEvent(self, e):
		self.scene().build_gate(self.mapToScene(e.pos()))
		e.accept()

	def dropEvent(self, e):
		self.scene().build_gate(None)
		gate_type = pickle.loads(e.mimeData().data('application/gate-type'))
		self.scene().add_gate(gate_type, self.mapToScene(e.pos()))
		e.accept()
