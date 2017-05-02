from .scene import UNIT
from . import glob

import math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


WIRE_CURVE = 1.5					# Controls the wire's curvature: higher = curvier
WIRE_MIN_OFFSET = 0.5				# Minimum control point offset for short wires, should be 0 < x <= 0.5
AVOID_PORTS = True					# Should the wires avoid intersecting ports? May trade aesthetics for clarity


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
		source = self.mapFromScene(self.start.center_scene_pos())
		sink = self.mapFromScene(self.end.center_scene_pos())
		path = self._path_between(source, sink)

		if AVOID_PORTS:
			path = self._move_at_intersections(source, sink, path)

		self.setPath(path)

	# Return the bezier curve (or spline) between the two points
	@classmethod
	def _path_between(cls, start, stop):
		path = QPainterPath()

		if start.x() < stop.x():
			delta = stop - start
			dist = math.sqrt(delta.x()**2 + delta.y()**2)
			offset = min(WIRE_MIN_OFFSET * dist, WIRE_CURVE * UNIT)
			path.moveTo(start)
			path.cubicTo(start + QPointF(offset, 0), stop - QPointF(offset, 0), stop)

		else:
			offset = WIRE_MIN_OFFSET * UNIT
			mid = (start + stop) / 2
			if abs(mid.y() - start.y()) < offset:
				mid.setY(start.y() + math.copysign(2 * offset, mid.y() - start.y()))

			spline = cls._spline((
				start,
				start + QPointF(offset, 0),
				QPointF(start.x() + offset, mid.y()),
				QPointF(stop.x() - offset, mid.y()),
				stop - QPointF(offset, 0),
				stop
			))

			for start, p1, p2, stop in spline:
				path.moveTo(start)
				path.cubicTo(p1, p2, stop)

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

		return bs

	def _move_at_intersections(self, start, stop, path):
		p = self._intersected_port(path)
		print("A", start, p, stop)
		if p:
			path1 = self._path_between(start, p)
			path2 = self._path_between(p, stop)
			print("B", start, p, stop)
			path = self._move_at_intersections(start, p, path1) + self._move_at_intersections(p, stop, path2)
		return path

	def _intersected_port(self, path):
		for g in self.scene().gates.values():
			for p in g.in_ports + g.out_ports:
				if p is not self.start and p is not self.end and path.intersects(p.rect()):
					return self._get_better_pos(path, p)
		return None

	@staticmethod
	def _get_better_pos(path, port):
		offset = 0.25 * QPointF(0, UNIT)
		return port.center_scene_pos() + offset

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
