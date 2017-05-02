from .scene import UNIT
from .iopanel import InputPanel, OutputPanel
from . import glob

import abc

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

FONT = QFont("Courier", 10)			# The font used for gate names etc.


class IOItem(QGraphicsProxyWidget, abc.ABC, metaclass=glob.AbstractWidgetMeta):
	def __init__(self, pos, width, circuit_size, panel_type, port_align, *args):
		super().__init__(*args)
		self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
		self.setZValue(1)
		self.setWidget(panel_type(circuit_size))
		self.setGeometry(QRectF(*pos, width, circuit_size * UNIT))
		rect = self.rect()

		x = 0 if port_align & Qt.AlignLeft else rect.width() if port_align & Qt.AlignRight else rect.width()/2
		ys = self.widget().get_port_ys()
		self.ports = tuple(PortItem(QPointF(x, ys[i]), self) for i in range(circuit_size))

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemScenePositionHasChanged:
			self.scene().scene_changed.emit()
		return QGraphicsProxyWidget.itemChange(self, change, value)


class InputItem(IOItem):
	def __init__(self, size, pos=(0, 0), *args):
		super().__init__(pos, 60, size, InputPanel, Qt.AlignRight, *args)


class OutputItem(IOItem):
	def __init__(self, size, pos=(0, 0), *args):
		super().__init__(pos, 30, size, OutputPanel, Qt.AlignLeft, *args)


class GateItem(QGraphicsRectItem):
	def __init__(self, gate, pos=(0, 0), *args):
		super().__init__(*pos, UNIT, len(gate) * UNIT, *args)
		self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
		self.gate = gate
		self.setBrush(QBrush(Qt.white))
		rect = self.rect()

		self.text = QGraphicsSimpleTextItem(str(gate), self)
		self.text.setFont(FONT)
		text_rect = self.text.boundingRect()
		self.text.setPos(rect.center().x() - text_rect.width()/2, rect.center().y() - text_rect.height()/2)

		ys = tuple((i + 0.5) * rect.height() / len(gate) for i in range(len(gate)))
		self.in_ports = tuple(PortItem(QPointF(0, ys[i]), self) for i in range(len(gate)))
		self.out_ports = tuple(PortItem(QPointF(rect.width(), ys[i]), self) for i in range(len(gate)))

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemScenePositionHasChanged:
			self.scene().scene_changed.emit()
		return QGraphicsItem.itemChange(self, change, value)


class PortItem(QGraphicsEllipseItem):
	SIZE = 8

	def __init__(self, center, *args):
		super().__init__(glob.create_square(center, self.SIZE), *args)
		self.center = center
		self.setBrush(QBrush(Qt.black))

	def center_scene_pos(self):
		return self.parentItem().scenePos() + self.center

