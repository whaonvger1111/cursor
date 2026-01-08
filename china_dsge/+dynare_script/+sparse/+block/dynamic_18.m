function [y, T, residual, g1] = dynamic_18(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10657)=exp(y(1167));
  residual(1)=(T(10657))-(T(167)*T(466)-T(463)*T(669));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10657);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
