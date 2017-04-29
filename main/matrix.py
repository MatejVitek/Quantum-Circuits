import cmath
from itertools import product

#this is a helpful external function that computes the tensor product of a list of matrices
#in the order given by the list
def tensor(matrixlist):
    T=(matrixlist[0]).bintensor(matrixlist[1])
    for i in range(2,len(matrixlist)):
        T=T.bintensor(matrixlist[i])

    return T   

def matrix_product(matrixlist):
    I=Matrix.Id(len(matrixlist[0]))
    for M in matrixlist:
        I=M*I
        
    return I

class MatrixError(Exception):
    """ An exception class for Matrix """
    pass

#class for matrices
class Matrix(object):
    def __init__(self, rows):
        if rows==[]:
            raise MatrixError('Please specify the rows of the matrix.')
        for i in range(len(rows)-1):
            if len(rows[i])!=len(rows[i+1]):
                raise MatrixError('Row dimensions are not consistent.')
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def __setitem__(self, i, item):
        self.rows[i]=item

    def __str__(self):
        string=''
        for i in self.rows:
            for j in i:
                string+=str(j)+' '
            string+='\n'

        return string

    def __repr__(self):
        s=str(self.rows)
        rep="Matrix: \"%s\"" % (s)
        return rep

    def __eq__(self, M):
        return (M.rows == self.rows)

    def __mul__(self, M):
        if len(self.rows[0])!=len(M):
            raise MatrixError('Matrix dimensions must agree.')

        result = Matrix([[0]*len(M.rows[0]) for x in range(len(self))])
        for i in range(len(self)):
            for j in range(len(M.rows[0])):
                column=[k[j] for k in M.rows]
                result[i][j] = sum([item[0]*item[1] for item in zip(self.rows[i], column)])

        return result
    
    #round all entries of the matrix to a number of places to prevent numerical malfunctions
    def Round(self, places):
        M=Matrix.Zero(len(self))
        for i in range(len(M)):
            for j in range(len(M.rows[0])):
                M[i][j]=round(self[i][j].real, places)
        return M

    def transpose(self):
        self.rows=[list(item) for item in zip(*self.rows)]
        
    def getConjugate(self):
        M=Matrix.Zero(len(self))
        for i in range(len(M)):
            for j in range(len(M.rows[0])):
                M[j][i]=(self[i][j]).conjugate()
        return M
    
    def isUnitary(self):
        if (self*(self.getConjugate())).Round(12)==Matrix.Id(len(self)):
            return True
        else:
            return False
    
    #returns the tensor product of self and M. Will mostly use tensor() function for tensor products
    #this is only the basis for it
    def bintensor(self,M):
        m=len(self)
        n=len(self.rows[0])
        p=len(M)
        q=len(M.rows[0])
        
        T=Matrix.Zero(m*p,n*q)
        
        for i in range(0,m*p,p):
            for j in range(0,n*q,q):
                for k in range(p):
                    for l in range(q):
                        T[i+k][j+l]=(self[int(i/p)][int(j/q)])*(M[k][l])
                        
        return T        
    
    #multiplies self(vector) with a list of matrices in the order of the list
    def apply(self, matrices):
        if len(self.rows[0])>1:
            raise MatrixError("This method is reserved for vectors.")
        
        M=Matrix.vector([0 for i in range(len(self))])
        for i in range(len(M)):
            M[i][0]=self[i][0]
                
        for N in matrices:
            M=N*M
            
        return M

    #these are class methods for quickly generating the matrices needed in the project.
    #Add more if needed.
    @classmethod
    def vector(cls, column):
        M=Matrix([column])
        M.transpose()
        return M
    
    @classmethod
    def Zero(cls,nrows,ncolumns=0):
        if ncolumns==0:
            ncolumns=nrows
        rows=[[0]*ncolumns for x in range(nrows)]
        return cls(rows)
        
    @classmethod
    def Id(cls,size):
        rows=[[0]*size for x in range(size)]
        for i in range(size):
            rows[i][i]=1

        return cls(rows)
    
    @classmethod
    def H(cls, size=1):
        seznam=[]
        if size==1:
            return cls([[2**(-0.5),2**(-0.5)],[2**(-0.5),-(2**(-0.5))]])
        else:
            for i in range(size):
                seznam.append(cls([[2**(-0.5),2**(-0.5)],[2**(-0.5),-(2**(-0.5))]]))
        return tensor(seznam)
    
    @classmethod
    def X(cls, size=1):
        seznam=[]
        if size==1:
            return cls([[0,1],[1,0]])
        else:
            for i in range(size):
                seznam.append(cls([[0,1],[1,0]]))
        return tensor(seznam)

    @classmethod
    def Y(cls, size=1):
        seznam=[]
        if size==1:
            return cls([[0,-1j],[0+1j,0]])
        else:
            for i in range(size):
                seznam.append(cls([[0,-1j],[0+1j,0]]))
        return tensor(seznam)

    @classmethod
    def Z(cls, size=1):
        seznam=[]
        if size==1:
            return cls([[1,0],[0,-1]])
        else:
            for i in range(size):
                seznam.append(cls([[1,0],[0,-1]]))
        return tensor(seznam)
    
    @classmethod
    def SqrtNot(cls, size=1):
        seznam=[]
        if size==1:
            return cls([[0.5*(1+1j),0.5*(1-1j)],[0.5*(1-1j),0.5*(1+1j)]])
        else:
            for i in range(size):
                seznam.append(cls([[0.5*(1+1j),0.5*(1-1j)],[0.5*(1-1j),0.5*(1+1j)]]))
        return tensor(seznam)

    @classmethod
    def PhaseShift(cls,phase,size=1):
        seznam=[]
        if size==1:
            return cls([[1,0],[0,cmath.e**(1j*(phase))]])
        else:
            for i in range(size):
                seznam.append(cls([[1,0],[0,cmath.e**(1j*(phase))]]))
        return tensor(seznam)
    
    @classmethod
    def QFT(cls,size=1):
        n=2**size
        M=cls.Zero(n)
        for i in range(n):
            for j in range(n):
                M[i][j]=(n**(-0.5))*(cmath.e**((i*j)*1j*2*cmath.pi/n))
     
        return M
    
    @classmethod
    def Permutation(cls,permutation):
        P=cls.Zero(2**(len(permutation)))
        
        for in_v in product(range(2),repeat=len(permutation)):
            in_v=list(in_v)
            out=[]
            for i in permutation:
                out.append(str(in_v[i]))
                
            for i in range(len(in_v)):
                in_v[i]=str(in_v[i])
            
            y=int('0b'+(''.join(in_v)),2)
            z=int('0b'+(''.join(out)),2)
            P[y][z]=1
                     
        return P

    @classmethod
    def Cnot(cls):
        return cls([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])

    @classmethod
    def T(cls):
        Toffoli=cls.Id(8)
        Toffoli.rows[6]=[0,0,0,0,0,0,0,1]
        Toffoli.rows[7]=[0,0,0,0,0,0,1,0]
        return Toffoli



