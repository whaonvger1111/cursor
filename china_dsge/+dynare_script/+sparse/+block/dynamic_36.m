function [y, T, residual, g1] = dynamic_36(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10675)=exp(y(951));
  residual(1)=(T(10675))-(T(149)*T(313)-T(310)*T(637));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10675);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
