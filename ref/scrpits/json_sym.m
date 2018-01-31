function out = json_sym(arr)
    out = string(sprintf('"%s" : %s',inputname(1),jsonencode(char(arr))));
end