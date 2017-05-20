from main.circuit import *
from random import randint
from math import gcd, log
import fractions      

def is_prime(n):
    if n==2 or n==3:
        return True
    for i in range(2,int(n**(1/2))+1):
        if n % i==0:
            return False
        
    return True
       

def approx(c, maxd):
    i=1
    x=fractions.Fraction.from_float(c).limit_denominator(i)
    while abs(c-x)>=1/(maxd):
        i+=1
        x=fractions.Fraction.from_float(c).limit_denominator(i)
        
    return(x)

def binary(n,p1,p2,p):
    b=bin(n)
    l=len(b)-2
    if p==l:
        return b[2+p1:p2+2]
    else:
        b=(p-l)*'0' + b[2:]
        return b[p1:p2]

def Shor(N):
    sez=[]
    while N!=1:
        if is_prime(N):
            sez.append(N)
            break
        
        a=randint(2,N-1)
        g=gcd(a,N)
        
        if g!=1:
            sez=sez+Shor(g)
            N=N//g
            continue
        
        else:
            q=(len(bin(N))-2)*2
                    
            c=Circuit(q)
            
            U=Matrix.Zero(2**q)
            for i in range(0,2**q):
                for j in range(0,2**q):
                    i1=binary(i,0,q//2,q)
                    i2=binary(i,q//2,q,q)
                    j1=binary(j,0,q//2,q)
                    j2=binary(j,q//2,q,q)
                    check=True
    
                    if int(i2,2)==0 and i1==j1 and a**(int(i1,2)) % N==int(j2,2):                
                        U[i][j]=1 
                        U[j][i]=1
                        break
                    elif i2=='1'*(q//2) and i1==j1:
                        l=binary(a**(int(i1,2)) % N,0,q//2,q//2)
                        for k in range(0,len(l)):
                            if l[k]==j2[k]:
                                check=False
                                break
                        if check:
                            U[i][j]=1  
                            U[j][i]=1
                            break
            count=0
            for row in U.rows:
                if row==[0]*(2**q):
                    U[count][count]=1
                    count+=1
                    continue
                count+=1      
                
            h=c.add_gate(H,q//2) 
            c.add_wires(c, [i for i in range(0,q//2)], h, [i for i in range(0,q//2)])
            u=c.add(Gate(U,'U',True))
            c.add_wires(h, [i for i in range(0,q//2)], u, [i for i in range(0,q//2)]) 
            c.add_wires(c, [i for i in range(q//2,q)], u, [i for i in range(q//2,q)])
            c.add_wires(u, [i for i in range(q//2,q)], c, [i for i in range(q//2,q)])
            QFT=Matrix.QFT(q//2)
            qft=c.add(Gate(QFT,'QFT', True))
            c.add_wires(u, [i for i in range(0,q//2)], qft, [i for i in range(0,q//2)])
            c.add_wires(qft, [i for i in range(0,q//2)], c, [i for i in range(0,q//2)])
            
            in_v=[0]*(q//2)+[1]*(q//2)
            r=0
            while r==0:
                seznam=(c.run(in_v))[0:q//2]
                stri=''
                for i in seznam:
                    stri+=str(i)
                r=int(stri,2)
                
            r=r/(2**(q//2))
            r=approx(r,2**(q//2))
            r=r.denominator
            if r % 2==1:
                continue
            elif a**(r//2) % N==N-1:
                continue
            
            M1=gcd(a**(r//2) +1,N)
            M2=gcd(a**(r//2) -1,N)
            
            if M1>M2:
                sez=sez+Shor(M1)
                N=N//(M1)
            else:
                sez=sez+Shor(M2)
                N=N//(M2)
            
    return sez   

def Shor_test(numbers):                   
    f = open('tests.txt', 'w')
    for n in range(2,numbers):
        f.write('Prime factors of '+str(n)+':'+str(Shor(n))+'\n')    
    
    f.close()
        