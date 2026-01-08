function [y, T, residual, g1] = dynamic_35(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10674)=exp(y(963));
  residual(1)=(T(10674))-(T(150)*T(322)-T(319)*T(639));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10674);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
