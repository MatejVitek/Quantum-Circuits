from main.circuit import *


# This is circuit (5) from the paper
if __name__ == '__main__':
	c = Circuit(6)

	cnot1 = CNot()
	c.add(cnot1)
	x1 = X()
	c.add(x1)
	cnot2 = CNot()
	c.add(cnot2)
	x2 = X()
	c.add(x2)
	t = T()
	c.add(t)
	cnot3 = CNot()
	c.add(cnot3)
	x3 = X()
	c.add(x3)

	c.add_wires(c.input[0:3:2], cnot1.in_ports)
	c.add_wires(cnot1.out_ports, (c.output[0], x1.in_ports[0]))

	c.add_wires(c.input[1:4:2], cnot2.in_ports)
	c.add_wires(cnot2.out_ports, (c.output[1], x2.in_ports[0]))

	c.add_wires((x1.out_ports[0], x2.out_ports[0], c.input[4]), t.in_ports)
	c.add_wires(t.out_ports[0:1], c.output[2:3])

	c.add_wires((t.out_ports[2], c.input[5]), cnot3.in_ports)
	c.add_wires(cnot3.out_ports, (c.output[4], x3.in_ports[0]))

	c.add_wire(x3.out_ports[0], c.output[5])

	print(c.check())
	c.basic_draw()
