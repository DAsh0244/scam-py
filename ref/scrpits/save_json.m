function str = save_json(file_name,vars,base_key)
    if ~exist('base_key')
        base_key = file_name;
    end
    fid = fopen(file_name, 'wt');
    str = ['{"netlist":"' base_key '", "contents":{'];
    for i=vars
        str = [str i ',' ];
    end
    str = [str(1:end-1) '}}'];
    fprintf(fid,"%s",str);
    fclose(fid);
end
