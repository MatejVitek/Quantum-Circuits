from main.circuit import *


if __name__ == '__main__':
	# This is circuit (5) from the paper
	c = Circuit(6)

	cnot1 = c.add_gate(CNot)
	x1 = c.add_gate(X)
	cnot2 = c.add_gate(CNot)
	x2 = c.add_gate(X)
	t = c.add_gate(T)
	cnot3 = c.add_gate(CNot)
	x3 = c.add_gate(X)

	c.add_wires(c.input[0:3:2], cnot1.in_ports)
	c.add_wires(cnot1.out_ports, (c.output[0], x1.in_ports[0]))

	c.add_wires(c.input[1:4:2], cnot2.in_ports)
	c.add_wires(cnot2.out_ports, (c.output[1], x2.in_ports[0]))

	c.add_wires((x1.out_ports[0], x2.out_ports[0], c.input[4]), t.in_ports)
	c.add_wires(t.out_ports[0:2], c.output[2:4])

	c.add_wires((t.out_ports[2], c.input[5]), cnot3.in_ports)
	c.add_wires(cnot3.out_ports, (c.output[4], x3.in_ports[0]))

	c.add_wire(x3.out_ports[0], c.output[5])

	print(c.check())
	c.basic_draw()



	# Custom circuit to test value propagation (and Uf's computation)
	c = Circuit(3)

	cnot = c.add_gate(CNot)
	x = c.add_gate(X)
	uf = c.add_gate(Uf, lambda x: 1-x)

	c.add_wires(c.input[0:2], cnot.in_ports)
	c.add_wire(c.input[2], x.in_ports[0])
	c.add_wire(cnot.out_ports[0], c.output[0])
	c.add_wires((cnot.out_ports[1], x.out_ports[0]), uf.in_ports)
	c.add_wires(uf.out_ports, c.output[1:3])

	for v in [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0], [1, 0, 1], [1, 1, 0], [1, 1, 1]]:
		print(c.run(v))