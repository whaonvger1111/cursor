function [y, T, residual, g1] = static_6(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(5340)=exp(y(719));
  T(5341)=T(840)*params(1)*T(5340)/T(1);
  residual(1)=(T(840))-(T(5341));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=(-T(5341));
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
