function [y, T, residual, g1] = dynamic_30(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10669)=exp(y(1023));
  residual(1)=(T(10669))-(T(155)*T(367)-T(364)*T(647));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10669);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
