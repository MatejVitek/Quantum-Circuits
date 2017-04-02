import circuit
from itertools import product

test1=False
test2=True

#test function for circuit (5) from the paper
def test_function(in_v):
    out=[0 for i in in_v]
    out[0]=in_v[0]
    out[1]=in_v[1]
    out[2]=int(not in_v[0])
    out[3]=int(not in_v[1])
    out[4]=int((not in_v[0])and(not in_v[1]))
    out[5]=int(in_v[0] or in_v[1])
    
    return out      

#this is circuit (5) from the paper
c = Circuit(6)

cnot1 = c.add_gate(CNot)
x1 = c.add_gate(X)
cnot2 = c.add_gate(CNot)
x2 = c.add_gate(X)
t = c.add_gate(T)
cnot3 = c.add_gate(CNot)
x3 = c.add_gate(X)

c.add_wires(c, (0, 2), cnot1, ())
c.add_wire(cnot1, 0, c, 0)
c.add_wire(cnot1, 1, x1, 0)

c.add_wires(c, (1, 3), cnot2, ())
c.add_wire(cnot2, 0, c, 1)
c.add_wire(cnot2, 1, x2, 0)

c.add_wire(x1, 0, t, 0)
c.add_wire(x2, 0, t, 1)
c.add_wire(c, 4, t, 2)
c.add_wires(t, (0, 1), c, (2, 3))

c.add_wire(t, 2, cnot3, 0)
c.add_wire(c, 5, cnot3, 1)
c.add_wire(cnot3, 0, c, 4)
c.add_wire(cnot3, 1, x3, 0)

c.add_wire(x3, 0, c, 5)

#test for method1
if test1:
    for in_v in product(range(2),repeat=2):
        in_v=list(in_v)
        in_v=in_v + [0,0,0,0]
        if test_function(in_v)==c.run_method1(in_v):
            print("Check.")
        else:
            print("Method1 failed for input: "+str(in_v))
     
#test for method2
if test2:
    for in_v in product(range(2),repeat=2):
        in_v=list(in_v)
        in_v=in_v + [0,0,0,0]
        if test_function(in_v)==c.run_method2(in_v):
            print("Check.")
        else:
            print("Method2 failed for input: "+str(in_v))


#another simple circuit. given the input [1, x, y] it should negate it. Given [0,x,y] it
#should only negate the first two qbits
b=Circuit(3)
cnot1 = b.add_gate(CNot)
b.add_wires(b, (0, 2), cnot1, ())
x1 = b.add_gate(X)
b.add_wire(b, 1, x1, 0)
b.add_wires(cnot1, (0, 1), b, (0,2))
b.add_wire(x1, 0, b, 1)
x2=b.add_gate(X)
b.add_wire(cnot1, 0, x2, 0)
b.add_wire(x2, 0, b, 0)
print(b.run_method1([0,0,0]))
print(b.run_method2([0,0,0]))