function [y, T, residual, g1] = static_42(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10150)=exp(y(144));
  residual(1)=(T(10150))-(T(227)*T(454)-T(451)*T(723));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10150);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
