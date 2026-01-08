function [y, T, residual, g1] = dynamic_23(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10662)=exp(y(1107));
  residual(1)=(T(10662))-(T(162)*T(421)-T(418)*T(660));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10662);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
