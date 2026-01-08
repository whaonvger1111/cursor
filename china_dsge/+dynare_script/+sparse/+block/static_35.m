function [y, T, residual, g1] = static_35(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10143)=exp(y(228));
  residual(1)=(T(10143))-(T(255)*T(515)-T(511)*T(730));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10143);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
