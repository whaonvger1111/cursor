function [y, T, residual, g1] = static_44(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10152)=exp(y(120));
  residual(1)=(T(10152))-(T(219)*T(437)-T(433)*T(721));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10152);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
