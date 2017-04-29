from main.circuit import *
from itertools import product
from random import randint, choice

test1=True
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
        result=c.run(in_v)
        if test_function(in_v)==result:
            print("Check.")
        else:
            print("Method1 failed for input: "+str(in_v))
     
#test for method2
if test2:
    for in_v in product(range(2),repeat=2):
        in_v=list(in_v)
        in_v=in_v + [0,0,0,0]
        result=c.run(in_v,2)
        if test_function(in_v)==result:
            print("Check.")
        else:
            print("Method2 failed for input: "+str(in_v))

def random_test(iterations):
    for it in range(iterations):
        size=randint(3,6)
        n_gates=randint(1,size)
        c=Circuit(size)
        av_comp=[c]
        av_in=[[i for i in range(size)]]
        for i in range(n_gates):
            gate=c.add(choice([X(1,"Gate "+str(i)),Y(1,"Gate "+str(i)),Z(1,"Gate "+str(i)),H(1,"Gate "+str(i)),CNot("Gate "+str(i)),T("Gate "+str(i))]))
            for in_wire in range(len(gate)):
                j=randint(0,len(av_comp)-1)
                component=av_comp[j]
                k=randint(0,len(av_in[j])-1)
                inputs=av_in[j][k]
                c.add_wire(component, inputs ,gate ,in_wire)
                del av_in[j][k]
                if av_in[j]==[]:
                    del av_in[j]
                    del av_comp[j]
                    
            av_comp.append(gate)
            av_in.append([i for i in range(len(gate))])
            
        for i in range(len(c)):
            j=randint(0,len(av_comp)-1)
            component=av_comp[j]
            k=randint(0,len(av_in[j])-1)
            inputs=av_in[j][k]
            c.add_wire(component, inputs ,c ,i)
            del av_in[j][k]
            if av_in[j]==[]:
                del av_in[j]
                del av_comp[j]
                
        for in_v in product(range(2),repeat=len(c)): 
            in_v=list(in_v)
            weights1=c.run_method1(in_v)
            weights2=c.run_method2(in_v)
            for k in range(len(weights1)):
                if round(weights1[k], 14)!= round(weights2[k], 14):
                    print("difference detected: "+str(weights1[k])+"; "+str(weights2[k]))
                    print("input vector was: "+str(in_v))
                    return c
            
    return "all tests passed"

    