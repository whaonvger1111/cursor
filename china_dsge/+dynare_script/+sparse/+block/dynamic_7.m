function [y, T, residual, g1] = dynamic_7(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(5864)=exp(y(1492));
  T(5865)=exp(y(2239));
  T(5866)=params(1)*T(5865)*T(5863);
  residual(1)=(T(5864))-(T(5866));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(5864);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
