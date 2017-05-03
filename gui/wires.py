from .scene import UNIT
from . import glob

import math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


WIRE_CURVE = 1.5					# Controls the wire's curvature: higher = curvier
WIRE_MIN_CP_OFFSET = 0.5			# Minimum first control point offset for short wires, should be x ∈ (0, 0.5]
WIRE_MIN_SPECIAL_OFFSET = 0.25		# Minimum offset for backward loops and port avoiding
AVOID_PORTS = False					# Should the wires avoid intersecting ports? May trade aesthetics for clarity


class WireItem(QGraphicsPathItem):
	def __init__(self, wire, start, end, *args):
		super().__init__(*args)
		self.wire = wire
		self.setZValue(-1)

		self.start = start
		self.end = end

		self._shape = None
		self.setPen(QPen(QBrush(Qt.black), 3))

	def determine_color(self):
		wire = self.wire
		visited_gates = set()
		color = Qt.black

		while True:
			# Stop if a port is unconnected.
			if wire is None:
				break

			# If the input panel was reached, determine the correct color.
			if wire.left is glob.circuit:
				color = glob.wire_colors[wire.lind]
				break

			# Stop if there's a cycle (prevent infinite loops).
			if wire.left is None or wire.left in visited_gates:
				break

			visited_gates.add(wire.left)
			wire = wire.left.in_wires[wire.lind]

		pen = self.pen()
		pen.setColor(color)
		self.setPen(pen)

	def update_path(self):
		source = self.start.center_scene_pos()
		sink = self.end.center_scene_pos()
		path = self._path_between(source, sink)

		if AVOID_PORTS:
			gates = self.scene().gates.values()
			in_ports = [p for g in gates for p in g.in_ports if p is not self.end]
			out_ports = [p for g in gates for p in g.out_ports if p is not self.start]
			path = self._circumvent_ports(source, sink, path, in_ports, out_ports)

		self.setPath(path)

	# Return the bezier curve (or spline) between the two points
	@classmethod
	def _path_between(cls, start, stop):
		if start.x() < stop.x():
			delta = stop - start
			dist = math.sqrt(delta.x()**2 + delta.y()**2)
			offset = QPointF(min(WIRE_MIN_CP_OFFSET * dist, WIRE_CURVE * UNIT), 0)
			path = QPainterPath(start)
			path.cubicTo(start + offset, stop - offset, stop)

		else:
			offset = QPointF(WIRE_MIN_SPECIAL_OFFSET * UNIT, 0)

			mid = (start + stop) / 2
			if abs(mid.y() - start.y()) < offset.x():
				mid.setY(start.y() + math.copysign(2 * offset.x(), mid.y() - start.y()))

			path = cls._spline((
				start,
				start + offset,
				QPointF(start.x(), mid.y()) + offset,
				QPointF(stop.x(), mid.y()) - offset,
				stop - offset,
				stop
			))

		return path

	@staticmethod
	def _spline(d):
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

	def _circumvent_ports(self, start, stop, path, in_ports, out_ports):
		p1, p2 = self._intersected_port(path, in_ports, out_ports)
		if p1 is None and p2 is None:
			return path

		if p1:
			in_ports.remove(p1)
			p1 = p1.center_scene_pos()
			p1, p2 = self._better_pos(p1, p1 + QPointF(UNIT, 0), start, stop)
		elif p2:
			out_ports.remove(p2)
			p2 = p2.center_scene_pos()
			p1, p2 = self._better_pos(p2 - QPointF(UNIT, 0), p2, start, stop)

		path1 = self._path_between(start, p1)
		path2 = self._path_between(p2, stop)

		path1 = self._circumvent_ports(start, p1, path1, in_ports, out_ports)
		path2 = self._circumvent_ports(p1, stop, path2, in_ports, out_ports)

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
		return p.y() > k * p.x() + n

	def setPen(self, *args):
		self.prepareGeometryChange()
		super().setPen(*args)

	def shape(self):
		if self._shape is None:
			self._shape = self._stroke_path()
		return self._shape

	def setPath(self, *args):
		self.prepareGeometryChange()
		self._shape = None
		super().setPath(*args)

	def _stroke_path(self):
		pen = QPen(QBrush(Qt.black), self.pen().widthF(), Qt.SolidLine)
		stroker = QPainterPathStroker()
		stroker.setCapStyle(pen.capStyle())
		stroker.setJoinStyle(pen.joinStyle())
		stroker.setMiterLimit(pen.miterLimit())
		stroker.setWidth(pen.widthF())
		return stroker.createStroke(self.path())