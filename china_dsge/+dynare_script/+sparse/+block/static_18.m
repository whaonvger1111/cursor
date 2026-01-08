function [y, T, residual, g1] = static_18(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10126)=exp(y(432));
  residual(1)=(T(10126))-(T(323)*T(660)-T(656)*T(747));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10126);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
