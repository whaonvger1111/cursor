function [y, T, residual, g1] = dynamic_45(y, x, params, steady_state, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(10684)=exp(y(843));
  residual(1)=(T(10684))-(T(140)*T(241)-T(238)*T(622));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(10684);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
