function [y, T, residual, g1] = dynamic_21(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10660)=exp(y(1131));
  residual(1)=(T(10660))-(T(164)*T(439)-T(436)*T(664));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10660);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
