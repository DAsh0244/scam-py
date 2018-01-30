#! /bin/env/ python
'''
Test fixture for comparing netlist files from results.
'''

import os 
import os.path as osp
import pickle
import json
import sympy as sym

from collections import namedtuple
_Element = namedtuple('_Element', 'Name Node1 Node2 Value')
_Vsource = namedtuple('_Vsource', 'Name Node1 Node2 Value')
_Isource = namedtuple('_Isource', 'Name Node1 Node2 Value')
_Opamp = namedtuple('_Opamp', 'Name Node1 Node2 Node3')

py_res_path = osp.join(os.curdir,'py_results.pkl')
matlab_res_path = osp.join(os.curdir,'matlab_results.json')

def read_py_result(py_result_file):
    with open(py_result_file,'rb') as f:
        ref = pickle.load(f)
    return ref
    
def read_matlab_result(matlab_res_file):
    with open(matlab_res_file,'r') as f:
        ref = json.loads(f.read())
    return ref 
    
if __name__ == '__main__':
    from pprint import pprint
    py_results = read_py_result(py_res_path)
    matlab_results = read_matlab_result(matlab_res_path)
    # print('Python Results:')
    # print(''*80)
    # pprint(py_res)
    # print(''*80)
    
    # print('')
    
    # print('Matlab Results')
    # print(''*80)
    # pprint(matlab_res)
    # print(''*80)
    # sym.init_printing(use_unicode=False, use_latex=False)

    # sym.pprint(py_res[list(py_res.keys())[0]]['Sol'])
    # print(sym.srepr((py_res[list(py_res.keys())[0]]['Sol']).as_mutable()))
    print('')
    # print(sym.srepr(sym.Matrix(sym.sympify(matlab_res[list(matlab_res.keys())[0]]['Sol'][7:-1]))))
    for py_netlist, mat_netlist in zip(py_results, matlab_results): 
        if py_netlist != mat_netlist:
            print('unsame netlist!')
            break
        mat_res = matlab_results[mat_netlist]
        py_res = py_results[py_netlist]
        for key in mat_res:
            if 'matrix' in mat_res[key]:
                res = py_res[key].equals(sym.Matrix(sym.sympify(mat_res[key][7:-1])))
            elif isinstance(py_res[key], tuple):
                res = py_res[key]._asdict() == mat_res[key]
            else:
                res = py_res[key] == mat_res[key]
            if res == False:
                print('(mat){key}:{val}'.format(key=key,val=mat_res[key]))
                print('(py){key}:{val}'.format(key=key,val=py_res[key]))
            print('{key}: {res}'.format(key=key, res=res))
    
