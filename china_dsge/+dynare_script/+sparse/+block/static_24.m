function [y, T, residual, g1] = static_24(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10132)=exp(y(360));
  residual(1)=(T(10132))-(T(299)*T(609)-T(605)*T(741));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10132);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
