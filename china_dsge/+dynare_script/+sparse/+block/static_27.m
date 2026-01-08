function [y, T, residual, g1] = static_27(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10135)=exp(y(324));
  residual(1)=(T(10135))-(T(287)*T(582)-T(579)*T(738));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10135);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
