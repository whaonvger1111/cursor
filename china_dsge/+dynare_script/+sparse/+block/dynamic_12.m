function [y, T, residual, g1] = dynamic_12(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10651)=exp(y(1239));
  residual(1)=(T(10651))-(T(173)*T(520)-T(517)*T(681));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10651);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
