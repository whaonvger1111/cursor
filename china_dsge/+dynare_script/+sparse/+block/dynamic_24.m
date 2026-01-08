function [y, T, residual, g1] = dynamic_24(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10663)=exp(y(1095));
  residual(1)=(T(10663))-(T(161)*T(556)-T(553)*T(566));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10663);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
