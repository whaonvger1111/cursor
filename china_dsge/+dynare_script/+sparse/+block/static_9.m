function [y, T, residual, g1] = static_9(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(5344)=(T(5340)/params(2460))^params(10)*(T(1)^params(11))^(1-params(10));
  T(5345)=exp(y(744));
  T(5346)=T(5345)^params(12);
  residual(1)=(T(5340)/params(2460))-(T(5344)*(T(5346))^(1-params(10))+x(2));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=(-(T(5344)*T(5345)*getPowerDeriv(T(5345),params(12),1)*getPowerDeriv(T(5346),1-params(10),1)));
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
