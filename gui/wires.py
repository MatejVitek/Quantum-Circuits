from .scene import UNIT
from . import glob

import math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


WIDTH = 3							# Wire width
WIRE_CURVE = 1.5					# Controls the wire's curvature: higher = curvier
WIRE_MIN_CP_OFFSET = 0.5			# Minimum first control point offset for short wires, should be x ∈ (0, 0.5]
WIRE_MIN_SPECIAL_OFFSET = 0.25		# Minimum offset for backward loops and port avoiding
AVOID_PORTS = True					# Should the wires avoid intersecting ports? May trade aesthetics for clarity


# Return the bezier curve (or spline) between two points
def path_between(start, stop):
	if start.x() < stop.x():
		delta = stop - start
		dist = math.sqrt(delta.x() ** 2 + delta.y() ** 2)
		offset = QPointF(min(WIRE_MIN_CP_OFFSET * dist, WIRE_CURVE * UNIT), 0)
		path = QPainterPath(start)
		path.cubicTo(start + offset, stop - offset, stop)

	else:
		offset = QPointF(WIRE_MIN_SPECIAL_OFFSET * UNIT, 0)

		mid = (start + stop) / 2
		if abs(mid.y() - start.y()) < offset.x():
			mid.setY(start.y() + math.copysign(2 * offset.x(), mid.y() - start.y()))

		path = spline((
			start,
			start + offset,
			QPointF(start.x(), mid.y()) + offset,
			QPointF(stop.x(), mid.y()) - offset,
			stop - offset,
			stop
		))

	return path


def spline(d):
	m = len(d) - 3
	bs = [[d[0], d[1], (d[1] + d[2])/2, None]]

	for l in range(m-2):
		bs.append([None, 2/3 * d[l+2] + 1/3 * d[l+3], 1/3 * d[l+2] + 2/3 * d[l+3], None])
	bs.append([None, 1/2 * d[-3] + 1/2 * d[-2], d[-2], d[-1]])

	for l in range(m-1):
		bs[l][3] = bs[l+1][0] = 1/2 * bs[l][2] + 1/2 * bs[l+1][1]

	path = QPainterPath()
	for start, p1, p2, stop in bs:
		path.moveTo(start)
		path.cubicTo(p1, p2, stop)

	return path


class WireItem(QGraphicsPathItem):
	def __init__(self, wire, start, end, *args):
		super().__init__(*args)
		self.wire = wire
		self.setZValue(-1)
		self.setFlag(QGraphicsItem.ItemIsSelectable)

		self.start = start
		self.end = end
		self.start.connect(self)
		self.end.connect(self)

		self._shape = None
		self._rect = None
		self.setPen(QPen(QBrush(Qt.black), WIDTH))

	def determine_color(self):
		if glob.circuit.contains_cycle():
			return

		wire = self.wire
		color = Qt.black

		while True:
			# Stop if a port is unconnected.
			if wire is None:
				break

			# If the input panel was reached, determine the correct color.
			if wire.left is glob.circuit:
				color = glob.wire_colors[wire.lind]
				break

			wire = wire.left.in_wires[wire.lind]

		pen = self.pen()
		pen.setColor(color)
		self.setPen(pen)

	def update_path(self):
		if not self.scene():
			return

		source = self.start.center_scene_pos()
		sink = self.end.center_scene_pos()
		path = path_between(source, sink)

		if AVOID_PORTS:
			gates = self.scene().gates.values()
			in_ports = {p for g in gates for p in g.in_ports if p is not self.end}
			out_ports = {p for g in gates for p in g.out_ports if p is not self.start}
			path = self._circumvent_ports(source, sink, path, in_ports, out_ports)

		self.setPath(path)

	def _circumvent_ports(self, start, stop, path, in_ports, out_ports):
		port1, port2 = self._intersected_port(path, in_ports, out_ports)
		if not port1 and not port2:
			return path

		if port1:
			in_ports.remove(port1)
			p1 = port1.center_scene_pos()
			try:
				p1, p2 = self._better_pos(p1, p1 + QPointF(UNIT, 0), start, stop)
			except ZeroDivisionError:
				p1 -= QPointF(WIRE_MIN_SPECIAL_OFFSET * UNIT, 0)
				p2 = QPointF(float('inf'), 0)

		elif port2:
			out_ports.remove(port2)
			p2 = port2.center_scene_pos()
			try:
				p1, p2 = self._better_pos(p2 - QPointF(UNIT, 0), p2, start, stop)
			except ZeroDivisionError:
				p1 = QPointF(float('-inf'), 0)
				p2 += QPointF(WIRE_MIN_SPECIAL_OFFSET * UNIT, 0)

		# Special case to avoid weird winding wires
		if start.x() > p1.x() or stop.x() < p2.x():
			if start.x() > p1.x() and p2.x() > stop.x():
				return path
			p = p2 if start.x() > p1.x() else p1
			offset = QPointF(WIRE_MIN_SPECIAL_OFFSET * UNIT, 0)
			path = spline((start, start + offset, p, stop - offset, stop))
			return self._circumvent_ports(start, stop, path, in_ports, out_ports)

		path1 = path_between(start, p1)
		path2 = path_between(p2, stop)
		path1 = self._circumvent_ports(start, p1, path1, in_ports, out_ports)
		path2 = self._circumvent_ports(p2, stop, path2, in_ports, out_ports)

		return path1 + path2

	@staticmethod
	def _intersected_port(path, in_ports, out_ports):
		for p in in_ports:
			if path.intersects(p.mapToScene(p.rect()).boundingRect()):
				return p, None
		for p in out_ports:
			if path.intersects(p.mapToScene(p.rect()).boundingRect()):
				return None, p
		return None, None

	@classmethod
	def _better_pos(cls, p1, p2, start, stop):
		offset = QPointF(0, WIRE_MIN_SPECIAL_OFFSET * UNIT)
		p = (p1 + p2) / 2
		if cls._above_line(p, start, stop):
			return p1 + offset, p2 + offset
		else:
			return p1 - offset, p2 - offset

	@staticmethod
	def _above_line(p, start, stop):
		k = (stop.y() - start.y()) / (stop.x() - start.x())
		n = stop.y() - k * stop.x()
		return p.y() < k * p.x() + n

	def setPen(self, *args):
		self.prepareGeometryChange()
		self._shape = None
		self._rect = None
		super().setPen(*args)

	def setPath(self, *args):
		self.prepareGeometryChange()
		self._shape = None
		self._rect = None
		super().setPath(*args)

	def shape(self):
		if self._shape is None:
			self._shape = self._stroke_path()
		return self._shape

	def _stroke_path(self):
		pen = QPen(QBrush(Qt.black), self.pen().widthF() + 15, Qt.SolidLine)
		stroker = QPainterPathStroker()
		stroker.setCapStyle(pen.capStyle())
		stroker.setJoinStyle(pen.joinStyle())
		stroker.setMiterLimit(pen.miterLimit())
		stroker.setWidth(pen.widthF())
		return stroker.createStroke(self.path())

	def boundingRect(self):
		if self._rect is None:
			self._rect = self._stroke_path().boundingRect()
		return self._rect

	def paint(self, qp, option, *args):
		selected = option.state & QStyle.State_Selected
		option.state &= ~QStyle.State_Selected
		super().paint(qp, option, *args)
		if selected:
			qp.setPen(QPen(Qt.black, 2))
			qp.setBrush(QBrush(Qt.white))

			start = self.start.center_scene_pos()
			end = self.end.center_scene_pos()
			offset = QPointF(min(15., max(10., (end.x() - start.x()) / 4)), 0)
			qp.drawConvexPolygon(start - QPointF(0, 5), start + QPointF(0, 5), start + offset)
			qp.drawConvexPolygon(end - QPointF(0, 5), end + QPointF(0, 5), end - offset)


class PartialWireItem(QGraphicsPathItem):
	def __init__(self, start, *args):
		super().__init__(*args)
		self.start = start
		self.reverse = False

		self._rect = None
		self.setPen(QPen(QBrush(Qt.black), WIDTH))

	def update_path(self, pos):
		source = self.start.center_scene_pos()
		if self.reverse:
			source, pos = pos, source
		path = path_between(source, pos)
		self.setPath(path)

	def setPen(self, *args):
		self.prepareGeometryChange()
		self._rect = None
		super().setPen(*args)

	def setPath(self, *args):
		self.prepareGeometryChange()
		self._rect = None
		super().setPath(*args)

	def boundingRect(self):
		if self._rect is None:
			self._rect = self.path().boundingRect()
		return self._rect
