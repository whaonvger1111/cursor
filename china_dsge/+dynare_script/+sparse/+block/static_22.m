function [y, T, residual, g1] = static_22(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10130)=exp(y(384));
  residual(1)=(T(10130))-(T(307)*T(625)-T(622)*T(743));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10130);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
