# scam.py
A python implementation of [scam.m][scam], a  matlab symbolic circuit solver script.

## dependencies:
  - [python3][py3] (no plan for py2 support)
  - [sympy][sympy] (should be as simply as "`pip install sympy`")
  - [numpy][numpy] (currently only used for reading netlist files -- will be taken out if no more productive use comes about in next version)
  (for windows, try the [precompiled binaries][py_win_bin], else try "`pip install numpy`")

## Usage:
```shell
scam.py <netlist-file-path>
```


## Changelog
* 25-Jan-2018 first implementation
* 29-Jan-2018 initial test suite created

[scam]: https://www.swarthmore.edu/NatSci/echeeve1/Ref/mna/MNA6.html
[sympy]: http://www.sympy.org/en/index.html
[numpy]: http://www.numpy.org/
[py_win_bin]: https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
[py3]: https://www.python.org/
