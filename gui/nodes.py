from .scene import UNIT
from .iopanel import InputPanel, OutputPanel
from . import utils

import abc

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

FONT = QFont("Courier", 10)			# The font used for gate names etc.


class IOItem(QGraphicsRectItem, abc.ABC, metaclass=utils.AbstractWidgetMeta):
	def __init__(self, width, circuit_size, panel_type, port_align, *args):
		super().__init__(QRectF(0, 0, width, circuit_size * UNIT), *args)

		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
		self.setZValue(1)
		self.setPen(QPen(Qt.NoPen))
		self.setBrush(QBrush(Qt.NoBrush))
		rect = self.rect()

		self.proxy = QGraphicsProxyWidget(self)
		self.widget = panel_type(circuit_size)
		self.proxy.setWidget(self.widget)
		self.proxy.setGeometry(rect)

		x = 0 if port_align & Qt.AlignLeft else rect.width() if port_align & Qt.AlignRight else rect.width()/2
		ys = self.widget.get_port_ys()
		self.ports = tuple(PortItem(QPointF(x, ys[i]), self) for i in range(circuit_size))

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemScenePositionHasChanged:
			self.scene().scene_changed.emit()
		return QGraphicsItem.itemChange(self, change, value)

	def mousePressEvent(self, *args):
		for item in self.scene().selectedItems():
			item.setSelected(False)
		super().mousePressEvent(*args)


class InputItem(IOItem):
	def __init__(self, size, *args):
		super().__init__(60, size, InputPanel, Qt.AlignRight, *args)


class OutputItem(IOItem):
	def __init__(self, size, *args):
		super().__init__(30, size, OutputPanel, Qt.AlignLeft, *args)


class GateItem(QGraphicsRectItem):
	def __init__(self, gate, *args):
		super().__init__(0, 0, UNIT, len(gate) * UNIT, *args)

		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
		self.gate = gate
		self.setBrush(QBrush(Qt.white))
		rect = self.rect()

		self.text = QGraphicsSimpleTextItem(self)
		self.text.setFont(FONT)
		self.update_text()

		ys = tuple((i + 0.5) * rect.height() / len(gate) for i in range(len(gate)))
		self.in_ports = tuple(PortItem(QPointF(0, ys[i]), self) for i in range(len(gate)))
		self.out_ports = tuple(PortItem(QPointF(rect.width(), ys[i]), self) for i in range(len(gate)))

	def update_text(self):
		self.text.setText(utils.shorten(str(self.gate)))
		rect = self.rect()
		text_rect = self.text.boundingRect()
		self.text.setPos(rect.center().x() - text_rect.width() / 2, rect.center().y() - text_rect.height() / 2)

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemScenePositionHasChanged:
			self.scene().scene_changed.emit()
		return QGraphicsItem.itemChange(self, change, value)


class PortItem(QGraphicsEllipseItem):
	SIZE = 8
	HL_SCALE = 1.5
	HL_BRUSH = QBrush(Qt.darkYellow)

	def __init__(self, center, *args):
		super().__init__(utils.create_square(center, self.SIZE), *args)
		self.wire = None
		self.setAcceptHoverEvents(True)

		self.center = center
		self.setTransformOriginPoint(self.center)
		self.setPen(QPen(Qt.NoPen))
		self.setBrush(QBrush(Qt.black))

	def center_scene_pos(self):
		return self.parentItem().scenePos() + self.center

	def connect(self, wire):
		self.wire = wire
		self.setAcceptHoverEvents(wire is None)
		self.set_highlight(False)

	def disconnect(self):
		self.connect(None)

	def set_highlight(self, hl=True):
		self.setScale(self.HL_SCALE if hl else 1)
		self.setBrush(self.HL_BRUSH if hl else QBrush(Qt.black))

	def hoverEnterEvent(self, *args):
		self.set_highlight(True)
		super().hoverEnterEvent(*args)

	def hoverLeaveEvent(self, *args):
		self.set_highlight(False)
		super().hoverLeaveEvent(*args)

	def mousePressEvent(self, e):
		if e.button() != Qt.LeftButton or not self.acceptHoverEvents():
			return super().mousePressEvent(e)
		e.accept()

	def mouseReleaseEvent(self, e):
		self.scene().build_wire(self)
		e.accept()
