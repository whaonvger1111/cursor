function [y, T, residual, g1] = static_32(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10140)=exp(y(264));
  residual(1)=(T(10140))-(T(267)*T(540)-T(536)*T(733));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10140);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
