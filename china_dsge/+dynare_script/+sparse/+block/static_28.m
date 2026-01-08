function [y, T, residual, g1] = static_28(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10136)=exp(y(312));
  residual(1)=(T(10136))-(T(283)*T(574)-T(570)*T(737));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10136);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
