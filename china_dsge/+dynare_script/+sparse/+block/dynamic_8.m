function [y, T, residual, g1] = dynamic_8(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(5867)=(exp(y(719))/params(2460))^params(10)*(T(2841)^params(11))^(1-params(10));
  T(5868)=exp(y(1491));
  T(5869)=T(5868)^params(12);
  residual(1)=(T(5861)/params(2460))-(T(5867)*(T(5869))^(1-params(10))+x(2));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=(-(T(5867)*T(5868)*getPowerDeriv(T(5868),params(12),1)*getPowerDeriv(T(5869),1-params(10),1)));
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
