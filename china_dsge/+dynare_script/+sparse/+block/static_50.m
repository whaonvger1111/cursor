function [y, T, residual, g1] = static_50(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10158)=exp(y(48));
  residual(1)=(T(10158))-(T(195)*T(386)-T(382)*T(715));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10158);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
