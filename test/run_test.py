#! /bin/env/ python
'''
Test fixture for comparing netlist files from results.
'''

import os 
import glob
import os.path as osp
import pickle
import json
import sympy as sym

results_path = osp.join(os.curdir, 'sim_results')

def get_all_files_alpha(path, ext):
    return sorted(list(glob.glob(osp.join(path,'*.'+ext))))


def read_py_result(py_result_file):
    with open(py_result_file,'rb') as f:
        ref = pickle.load(f)
    return ref


def read_matlab_result(matlab_res_file):
    with open(matlab_res_file,'r') as f:
        ref = json.loads(f.read())
    return ref 


def compare_results(py_results, matlab_results):
    py_netlist, mat_netlist = py_results['netlist'], matlab_results['netlist']
    print('checking: {}'.format(py_netlist))
    if py_netlist != mat_netlist:
        raise ValueError('netlists are not corresponding!')
    py_res , mat_res = py_results['contents'], matlab_results['contents']
    good = True
    for key in mat_res:
        if 'matrix' in mat_res[key]:
            res = py_res[key].equals(sym.Matrix(sym.sympify(mat_res[key][7:-1])))
        else:
            res = py_res[key] == mat_res[key]
        if res == False:
            good = False
            print('[mat] {key}:{val}'.format(key=key,val=mat_res[key]))
            print(' [py] {key}:{val}'.format(key=key,val=py_res[key]))
        print('{key}: {res}'.format(key=key, res=res))
    return good
    
    
if __name__ == '__main__':
    for py_res_path, mat_res_path in zip(get_all_files_alpha(results_path,'pkl'),get_all_files_alpha(results_path,'json')):
        py_results = read_py_result(py_res_path)
        matlab_results = read_matlab_result(mat_res_path)
        compare_results(py_results, matlab_results)
        print('')
