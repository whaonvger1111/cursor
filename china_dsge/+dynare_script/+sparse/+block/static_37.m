function [y, T, residual, g1] = static_37(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10145)=exp(y(204));
  residual(1)=(T(10145))-(T(247)*T(497)-T(493)*T(728));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10145);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
