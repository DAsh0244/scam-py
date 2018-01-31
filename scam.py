#! /bin/env python3
'''
python port of scam.m a matlab script for arbitrary symbolic nodal analysis 
from scam.m
%This program takes a netlist (similar to SPICE), parses it to derive the
%circuit equations, then solves them symbolically.  
%
%Full documentation available at www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA1.html
%
'''

__author__ = 'Danyal Ahsanullah'
__email__ = 'danyal.ahsanullah@gmail.com'

__version_info__ = (0,1,1)
__version__ = '.'.join(map(str, __version_info__))

# maybe needed for sympy.preview function
# import os
# os.environ['PYGLET_SHADOW_WINDOW']="0"

import numpy as np
import sympy as sym
from datetime import datetime, timedelta
from collections import namedtuple
from itertools import chain

# _PASSIVE = 'RLC'
# _SUPPORTED = _PASSIVE + 'OVI'
_UNSUPPORTED = 'QDZ'
RUNTIME = timedelta(0)

# record containers for differing circuit elements
_Element = namedtuple('_Element', 'Name Node1 Node2 Value')
_Vsource = namedtuple('_Vsource', 'Name Node1 Node2 Value')
_Isource = namedtuple('_Isource', 'Name Node1 Node2 Value')
_Opamp = namedtuple('_Opamp', 'Name Node1 Node2 Node3')

# some flag that i can prolly axe -- controls printing a first time info msg i think
FirstTime_rjla = True

# sympy print init -- still prints weird on my console unless disable unicode,
# and even then it seems to be limited to the 80 char console limit even if i use a larger console
# sym.init_printing()
# sym.init_printing(use_latex=False)
# sym.init_printing(use_unicode=False, use_latex=False)

# may end up using something like this for building data matrix,
# bytearray append/extend for building string and then a final conversion for feeding to sympy
# should avoid str reallocation and sympify-ing on every build 
# class StrMatrix:
    # """matrix of byte arrays for dynamically building strings in the form of a matrix"""
    # def __init__(self, row,col, initial='0', encoding='ascii', *args, **kwargs):
        # self.encoding = encoding
        # self.data = [[bytearray(initial, encoding) for i in range(col)] for i in range(row)]
    # def __getitem__(self, index):
        # return self.data[index[0]][index[1]]
    


def scam(fname):
    global FirstTime_rjla
    global RUNTIME 
    
    if FirstTime_rjla:
        print('scam.py - a python port of scam.m')
        print('Full documentation available at www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA1.html')
    
    print('\n\nStarted -- please be patient.\n\n', end='')
    
    with open(fname,'r') as file:
        d = np.loadtxt(file, delimiter=' ', 
           dtype={'names': ('Name', 'N1', 'N2', 'ARG3'),
           'formats': ('U15', 'i4', 'i4', 'U15')})    

    # for row in d:
        # print('Name:{Name} N1:{N1} N2:{N2} arg3:{arg3}'.format(Name=row['Name'], 
                                                               # N1=row['N1'], 
                                                               # N2=row['N2'], 
                                                               # arg3=row['arg3']))
    
    # crude timer
    start_time = datetime.now()
    
    # Initialize
    numNode = 0  # Number of nodes, not including ground (node 0).
    Elements = []
    Vsources = []
    Opamps = []
    Isources = []
    
    # Parse the input file
    for name, n1, n2, arg3 in d:
        desig = name[0]
        if desig in 'RLC':  # passive elements
            try:
                val = float(arg3)
            except ValueError:
                val = np.nan
            Elements.append(_Element(Name=name, Node1=n1, Node2=n2, Value=val))
        elif desig == 'V':  # voltage sources
            try:
                val = float(arg3)
            except ValueError:
                val = np.nan
            Vsources.append(_Vsource(Name=name, Node1=n1, Node2=n2, Value=val))
        elif desig == 'I':  #current sources
            try:
                val = float(arg3)
            except ValueError:
                val = np.nan
            Isources.append(_Isource(Name=name, Node1=n1, Node2=n2, Value=val))
        elif desig == 'O':  # opamps
            Opamps.append(_Opamp(Name=name, Node1=n1, Node2=n2, Node3=arg3))
        elif desig in _UNSUPPORTED:
            raise ValueError('Unsupported component type {!s}'.format(name))
        else:
            raise ValueError('Unknown component type {!s}'.format(name))
        numNode = max(n1,n2,numNode)
    numElem = len(Elements)
    numV = len(Vsources)
    numI = len(Isources)
    numO = len(Opamps)
    nodes = list(range(numNode)) # have to iterate multiple times, build once iterate multi 

    # Preallocate matrices #################################
    G = sym.zeros(numNode,numNode)
    V = sym.zeros(numNode,1)
    I = sym.zeros(numNode,1)
    if (numV+numO)!=0:
        B = sym.zeros(numNode,numV+numO)
        C = sym.zeros(numV+numO,numNode)
        D = sym.zeros(numV+numO,numV+numO)
        E = sym.zeros(numV+numO,1)
        J = sym.zeros(numV+numO,1)
    # Done preallocating matrices  -------------------------------------

    # Fill the G matrix ##################################################
    # Initially, make the G Matrix all zeros.
    # -- handled in prealloc
    # Now fill the G matrix with conductances from netlist
    for element in Elements:
        n1 = element.Node1 - 1
        n2 = element.Node2 - 1
        desig = element.Name[0]
        # Make up a string with the conductance of current element.
        if desig == 'R':
                g = '1/{}'.format(element.Name)
        elif desig == 'L':
                g = '1/s/{}'.format(element.Name)
        elif desig == 'C':
                g = 's*{}'.format(element.Name)
        else:
            raise ValueError('Unknown component type {!s}'.format(element.Name))

        # If neither side of the element is connected to ground
        # then subtract it from appropriate location in matrix.
        if n1 != -1 and n2 !=  -1:
            G[n1,n2] = '{}-{}'.format(G[n1,n2],g)
            G[n2,n1] = '{}-{}'.format(G[n2,n1],g)
        
        # If node 1 is connected to ground, add element to diagonal
        # of matrix.
        if n1 != -1:
            G[n1,n1] = '{}+{}'.format(G[n1,n1],g)
        # Ditto for node 2.
        if n2 != -1:
            G[n2,n2] = '{}+{}'.format(G[n2,n2],g)
    # The G matrix is finished -------------------------------------------   

    # Fill the I matrix ##################################################
    for j in nodes:
        for isource in Isources:
            if isource.Node1 == j+1:
                I[j] = '{}-{}'.format(I[j],isource.Name)
            elif isource.Node2 == j+1:
                I[j] = '{}+{}'.format(I[j],isource.Name)
    # The I matrix is done -----------------------------------------------

    # Fill the V matrix ##################################################
    for i in nodes:
        V[i] = 'v_{}'.format(i+1)
    # The V matrix is finished -------------------------------------------

    # other matrix stuff
    if (numV+numO) != 0:
        # %Fill the B matrix ##################################################
        # %Initially, fill with zeros.        
        # -- handled in prealloc
        # %First handle the case of the independent voltage sources.
        for i, vsource in enumerate(Vsources):  # Go through each independent source.
            for j in nodes:           # Go through each node.
                if vsource.Node1 == j+1:           # If node is first node,
                    B[j,i] = '1'               # then put '1' in the matrices.
                elif vsource.Node2 == j+1:         # If second node, put -1.
                    B[j,i] = '-1'
        
        # %Now handle the case of the Op Amp
        for i, opamp in enumerate(Opamps):
            for j in nodes:
                if opamp.Node3 == j+1:
                    B[j,i+numV] = '1'
                else:
                    B[j,i+numV] = '0'
        # %The B matrix is finished -------------------------------------------
        
        
        # %Fill the C matrix ##################################################
        # %Initially, fill with zeros.        
        # -- handled in prealloc
        # %First handle the case of the independent voltage sources.
        for i, vsource in enumerate(Vsources):  # Go through each independent source.
            for j in nodes:           # Go through each node.
                if vsource.Node1 == j+1:           # If node is first node,
                    C[i,j] = '1'               # then put '1' in the matrices.
                elif vsource.Node2 == j+1:         # If second node, put -1.
                    C[i,j] = '-1'

        # %Now handle the case of the Op Amp
        for i, opamp in enumerate(Opamps):
            for j in nodes:
                if opamp.Node1 == j+1:
                    C[i+numV,j] = '1'
                elif opamp.Node2 == j+1:
                    C[i+numV,j] = '-1'
                else:
                    C[i+numV,j] = '0'
        # %The C matrix is finished ------------------------------------------

        # %Fill the D matrix ##################################################
        # %The D matrix is non-zero only for CCVS and VCVS (not included
        # %in this simple implementation of SPICE)
        #
        # future Code Here
        #
        # %The D matrix is finished -------------------------------------------
        
        # %Fill the E matrix ##################################################
        # Starts with all zeros
        # -- handled in prealloc
        for i,vsource in enumerate(Vsources):
            E[i] = vsource.Name
        # %The E matrix is finished -------------------------------------------
        
        # %Fill the J matrix ##################################################
        for i,vsource in enumerate(Vsources):
            J[i]= 'I_{}'.format(vsource.Name)
        for i, opamp in enumerate(Opamps):
            J[i+numV] = 'I_{}'.format(opamp.Name)
        # %The J matrix is finished -------------------------------------------

        # G = Matrix([['0+1/R1+1/s/L1', '0-1/R1', '0-1/s/L1'],
        #             ['0-1/R1', '0+1/R1+1/R2+1/s/L2', '0-1/R2'],
        #             ['0-1/s/L1', '0-1/R2', '0+1/R2+1/s/L1+1/s/L3']]
        #           )
        # D = Matrix([0])
        # B = Matrix([[1],[0],[0]])
        # C = Matrix([[1,0,0]])
        # A = (G.row_join(B)).col_join(C.row_join(D))

        # %Form the A, X, and Z matrices (As cell arrays of strings).
        A = G.row_join(B).col_join(C.row_join(D))
        X = V.col_join(J)
        Z = I.col_join(E)
    else:
        A = G
        X = V
        Z = I

    # Solve matrix equation - this is the meat of the algorithm.   
    V = sym.factor(A.inv()*Z)

    # %Evaluate each of the unknowns in the matrix X.
    # nodes = dict()
    # for var, val in zip(X[:],V[:]):
        # nodes[str(var)] = val 

    # sub in values: 
    Sol = sym.cancel(V.subs([(elem.Name, elem.Value) for elem in chain(Elements,Vsources,Isources) if elem.Value is not np.nan]))

    print('Done! Elapsed time = {!s}.'.format(datetime.now()-start_time))
    # this_run = datetime.now()-start_time
    # print('Done! Elapsed time = {!s}.'.format(this_run))
    # RUNTIME += this_run
    
    print('Netlist')
    for row in d:
        print('{Name} {N1} {N2} {arg3}'.format(Name=row['Name'], N1=row['N1'], 
                                               N2=row['N2'], arg3=row['ARG3']))
    
    print('\nSolved variables:')
    for entry in X[:]:
        print(entry)
    print('')
    
    if FirstTime_rjla:
        print('scam.py - a python port of scam.m')
        print('Full documentation available at www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA1.html')
        FirstTime_rjla = False
    # print(Sol)
    # because scam.m was a script to run and use in matlab cmd window, have to return a bunch of things
    return Sol, V, A, X, Z, nodes, Elements,Vsources,Isources


if __name__ == '__main__':
    import os 
    import sys
    import pickle
    from code import interact 
    # import time
    # def timing(f, n, a):
        # global RUNTIME
        # r = range(n)
        # for i in r:
            # f(a); f(a); f(a); f(a); f(a); f(a); f(a); f(a); f(a); f(a)
        # print('')
        # print(f.__name__, 'avg:',  end='')
        # print(RUNTIME/(10*n))
    
    rets = ['Sol','V','A','X','Z','nodes','Elements','Vsources','Isources']
    fname = sys.argv[1]
    Sol, V, A, X, Z, nodes, Elements,Vsources,Isources = scam(fname)
    # interact(local=dict(globals(), **locals()))
    # timing(scam, 3,sys.argv[1])

    # outfile = '_'.join([os.path.splitext(fname)[0],'results.pkl' ])
    outfile = os.path.join('test','sim_results','{}_python.pkl'.format(os.path.splitext(os.path.basename(fname))[0]))
    Elements = [{key: val if val is not np.nan else [] for key,val in val._asdict().items()} for val in Elements]
    Isources = [{key: val if val is not np.nan else [] for key,val in val._asdict().items()} for val in Isources]
    Vsources = [{key: val if val is not np.nan else [] for key,val in val._asdict().items()} for val in Vsources]
    Elements = Elements[0] if len(Elements) == 1 else Elements
    Isources = Isources[0] if len(Isources) == 1 else Isources
    Vsources = Vsources[0] if len(Vsources) == 1 else Vsources
    d = { 'netlist':os.path.basename(fname), 'contents': {name:eval(name) for name in rets}}
    with open(outfile, 'wb') as file:
        pickle.dump(d, file)
    
    sys.exit()