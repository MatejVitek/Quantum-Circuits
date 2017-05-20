import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class View(QGraphicsView):
	view_changed = pyqtSignal(name='viewChanged')

	def __init__(self, *args):
		super().__init__(*args)
		self.scene().new_circuit.connect(self.center)
		self.scene().scene_changed.connect(self.view_changed)
		self.setRenderHint(QPainter.Antialiasing)
		self.setAcceptDrops(True)

		self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setDragMode(QGraphicsView.ScrollHandDrag)
		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

	def showEvent(self, *args):
		super().showEvent(*args)
		self.center()

	def setScene(self, *args):
		self.scene().new_circuit.disconnect(self.center)
		self.scene().scene_changed.disconnect(self.view_changed)
		super().setScene(*args)
		self.scene().new_circuit.connect(self.center)
		self.scene().scene_changed.connect(self.view_changed)
		self.view_changed.emit()

	def center(self):
		self.centerOn(self.scene().itemsBoundingRect().center())
		self.view_changed.emit()

	def fit_to_scene(self):
		self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)
		self.view_changed.emit()

	def wheelEvent(self, e):
		degrees = e.angleDelta().y() / 8.
		steps = degrees / 15.
		scale = 1.1 ** steps
		self.scale(scale, scale)
		self.view_changed.emit()
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
		self.parent().parent().refresh_panels()

	def mouseMoveEvent(self, e):
		super().mouseMoveEvent(e)
		if e.buttons() == Qt.LeftButton:
			self.viewport().setCursor(Qt.ClosedHandCursor)
		else:
			self.viewport().unsetCursor()
			if self.scene().partial_wire is not None:
				self.scene().partial_wire.update_path(self.mapToScene(e.pos()))

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
