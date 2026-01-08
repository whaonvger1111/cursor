function [y, T, residual, g1] = static_48(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10156)=exp(y(72));
  residual(1)=(T(10156))-(T(203)*T(403)-T(399)*T(717));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10156);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
