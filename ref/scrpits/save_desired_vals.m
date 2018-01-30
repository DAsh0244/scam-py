file_path = '../../test/matlab_results.json';

if ~exist('Isource')
    Isource = [];
end
if ~exist('Vsource')
    Vsource = [];
end
if ~exist('Element')
    Element = [];
end
if ~exist('Isource')
    Isource = [];
end
Sol = eval(V);
nodes = 0:numNode-1;
[filepath,name,ext] = fileparts(fname);
rets = [json_sym(Sol),json_sym(A),json_sym(V),json_sym(X),json_sym(Z),...
  ['"nodes":' jsonencode(nodes)], ['"Elements":' jsonencode(Element)],...
  ['"Vsources":' jsonencode(Vsource)],['"Isources":' jsonencode(Isource)]];
save_json(file_path, rets, [name ext]);
