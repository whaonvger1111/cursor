function [y, T, residual, g1] = dynamic_32(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10671)=exp(y(999));
  residual(1)=(T(10671))-(T(153)*T(349)-T(346)*T(643));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10671);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
