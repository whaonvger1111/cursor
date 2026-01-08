function [y, T, residual, g1] = static_2(y, x, params, sparse_rowval, sparse_colval, sparse_colptr, T)
residual=NaN(1, 1);
  T(1)=exp(y(720));
  residual(1)=(T(1))-(params(348)+params(340)+params(332)+params(324)+params(316)+params(308)+params(300)+params(292)+params(284)+params(276)+params(268)+params(260)+params(252)+params(244)+params(236)+params(228)+params(220)+params(212)+params(204)+params(196)+params(188)+params(180)+params(172)+params(164)+params(156)+params(148)+params(140)+params(132)+params(124)+params(116)+params(108)+params(100)+params(92)+params(84)+params(76)+params(68)+params(60)+params(52)+params(44)+params(36)+params(20)+params(28));
if nargout > 3
    g1_v = NaN(1, 1);
g1_v(1)=T(1);
    if ~isoctave && matlab_ver_less_than('9.8')
        sparse_rowval = double(sparse_rowval);
        sparse_colval = double(sparse_colval);
    end
    g1 = sparse(sparse_rowval, sparse_colval, g1_v, 1, 1);
end
end
