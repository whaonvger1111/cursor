function [y, T, residual, g1] = dynamic_5(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(5861)=exp(y(1466));
  T(5862)=params(1)*T(3064)*T(5861)/T(834);
  residual(1)=(T(1))-(T(5862));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=(-T(5862));
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
