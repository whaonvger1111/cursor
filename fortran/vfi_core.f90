module vfi_core
    implicit none
    
contains

! ============================================================
! 辅助函数
! ============================================================

    subroutine myfind_loc_fortran(x_grid, nx, xi, jl, omega)
        ! 找到jl使得x_grid(jl)<=xi<x_grid(jl+1)
        integer, intent(in) :: nx
        real(kind=8), dimension(nx), intent(in) :: x_grid
        real(kind=8), intent(in) :: xi
        integer, intent(out) :: jl
        real(kind=8), intent(out) :: omega
        integer :: i
        
        ! 二分查找
        jl = 0
        do i = 1, nx - 1
            if (x_grid(i) <= xi .and. xi < x_grid(i+1)) then
                jl = i - 1  ! Python索引从0开始
                exit
            end if
        end do
        
        ! 边界处理
        if (xi <= x_grid(1)) then
            jl = 0
        else if (xi >= x_grid(nx)) then
            jl = nx - 2
        end if
        
        ! 计算权重
        if (jl + 1 < nx) then
            omega = (x_grid(jl + 2) - xi) / (x_grid(jl + 2) - x_grid(jl + 1))
        else
            omega = 0.0d0
        end if
    end subroutine myfind_loc_fortran

    function myinterp1_fortran(x_grid, y_grid, nx, xi) result(yi)
        ! 一维线性插值
        integer, intent(in) :: nx
        real(kind=8), dimension(nx), intent(in) :: x_grid
        real(kind=8), dimension(nx), intent(in) :: y_grid
        real(kind=8), intent(in) :: xi
        real(kind=8) :: yi
        integer :: jl
        real(kind=8) :: omega
        
        call myfind_loc_fortran(x_grid, nx, xi, jl, omega)
        
        if (jl + 1 < nx) then
            yi = omega * y_grid(jl + 1) + (1.0d0 - omega) * y_grid(jl + 2)
        else
            yi = y_grid(nx)
        end if
    end function myinterp1_fortran

    function adjcost_scal_fortran(kprime, k, theta, delta) result(adj)
        ! 标量版本的调整成本
        real(kind=8), intent(in) :: kprime, k, theta, delta
        real(kind=8) :: adj
        
        adj = kprime - (1.0d0 - delta) * k
        if (kprime < (1.0d0 - delta) * k) then
            adj = theta * adj
        end if
    end function adjcost_scal_fortran

! ============================================================
! 无约束企业VFI: sub_V1_onestep
! ============================================================

    subroutine sub_V1_onestep_fortran(V1, pi_x, profit_mat, k_grid, q, theta, delta, psi, &
                                      V2, kpol_ind, nk, nx)
        ! 无约束企业价值函数V(k,x)的单步Bellman算子
        integer, intent(in) :: nk, nx
        real(kind=8), dimension(nk, nx), intent(in) :: V1
        real(kind=8), dimension(nx, nx), intent(in) :: pi_x
        real(kind=8), dimension(nk, nx), intent(in) :: profit_mat
        real(kind=8), dimension(nk), intent(in) :: k_grid
        real(kind=8), intent(in) :: q, theta, delta, psi
        real(kind=8), dimension(nk, nx), intent(out) :: V2
        integer, dimension(nk, nx), intent(out) :: kpol_ind
        
        integer :: x_c, k_c, kp_c, xp_c
        real(kind=8), dimension(nk, nk) :: RHS, adjcost_mat
        real(kind=8), dimension(nk, nx) :: V1_max, EV
        real(kind=8), dimension(nk) :: EV_x, profit_x, kprime_vec
        real(kind=8) :: max_val
        integer :: max_ind
        real(kind=8) :: kprime_val, k_today_val, adj_val, rhs_val
        
        ! 注意：EV计算现在在Python中使用BLAS优化的矩阵乘法完成
        ! 这里保留V1_max计算以备将来需要
        !$omp parallel do private(kp_c, x_c)
        do kp_c = 1, nk
            do x_c = 1, nx
                V1_max(kp_c, x_c) = max(theta * (1.0d0 - delta) * k_grid(kp_c), V1(kp_c, x_c))
            end do
        end do
        !$omp end parallel do
        
        ! EV = V1_max @ pi_x.T
        ! 注意：pi_x(i, j) = P(x'=j | x=i)，所以EV = V1_max @ pi_x.T
        ! EV(k, x) = sum_{x'} V1_max(k, x') * pi_x(x, x') = sum_{x'} V1_max(k, x') * P(x'=x' | x=x)
        ! 这个计算现在在Python中使用BLAS完成，但为了保持接口兼容性，
        ! 我们仍然在Fortran中计算（虽然较慢）。理想情况下应该修改接口传入EV。
        ! 使用OpenMP并行化的优化循环（比BLAS慢，但保持兼容性）
        EV = 0.0d0
        !$omp parallel do private(x_c, kp_c, xp_c)
        do x_c = 1, nx
            do kp_c = 1, nk
                do xp_c = 1, nx
                    ! 修复：使用pi_x(x_c, xp_c)而不是pi_x(xp_c, x_c)
                    ! pi_x(x_c, xp_c) = P(x'=xp_c | x=x_c)，这是正确的
                    EV(kp_c, x_c) = EV(kp_c, x_c) + V1_max(kp_c, xp_c) * pi_x(x_c, xp_c)
                end do
            end do
        end do
        !$omp end parallel do
        
        kprime_vec = k_grid
        
        ! 进行最大化（使用OpenMP并行化）
        !$omp parallel do private(x_c, EV_x, profit_x, kp_c, k_c, kprime_val, k_today_val, &
        !$omp& max_val, max_ind, adj_val, rhs_val)
        do x_c = 1, nx
            EV_x = EV(:, x_c)
            profit_x = profit_mat(:, x_c)
            
            ! 构建RHS矩阵 (nk, nk)
            ! 向量化计算调整成本
            do kp_c = 1, nk
                kprime_val = kprime_vec(kp_c)
                do k_c = 1, nk
                    k_today_val = k_grid(k_c)
                    ! 计算调整成本（内联，避免函数调用开销）
                    adj_val = kprime_val - (1.0d0 - delta) * k_today_val
                    if (kprime_val < (1.0d0 - delta) * k_today_val) then
                        adj_val = theta * adj_val
                    end if
                    
                    ! 构建RHS
                    rhs_val = profit_x(kp_c) - adj_val + &
                              q * (psi * theta * (1.0d0 - delta) * kprime_val + &
                                   (1.0d0 - psi) * EV_x(kp_c))
                    RHS(kp_c, k_c) = rhs_val
                end do
            end do
            
            ! 找到最大值及其索引 (沿着第0维，即行方向)
            do k_c = 1, nk
                max_val = RHS(1, k_c)
                max_ind = 1
                do kp_c = 2, nk
                    if (RHS(kp_c, k_c) > max_val) then
                        max_val = RHS(kp_c, k_c)
                        max_ind = kp_c
                    end if
                end do
                V2(k_c, x_c) = max_val
                kpol_ind(k_c, x_c) = max_ind - 1  ! Python索引从0开始
            end do
        end do
        !$omp end parallel do
    end subroutine sub_V1_onestep_fortran

! ============================================================
! 无约束企业VFI（快速版本，接受已计算的EV）
! ============================================================

    subroutine sub_V1_onestep_fortran_fast(V1, EV, profit_mat, k_grid, q, theta, delta, psi, &
                                          V2, kpol_ind, nk, nx)
        ! 无约束企业价值函数V(k,x)的单步Bellman算子（快速版本）
        ! EV已在Python中使用BLAS计算，直接使用
        integer, intent(in) :: nk, nx
        real(kind=8), dimension(nk, nx), intent(in) :: V1
        real(kind=8), dimension(nk, nx), intent(in) :: EV  ! 已计算的期望值
        real(kind=8), dimension(nk, nx), intent(in) :: profit_mat
        real(kind=8), dimension(nk), intent(in) :: k_grid
        real(kind=8), intent(in) :: q, theta, delta, psi
        real(kind=8), dimension(nk, nx), intent(out) :: V2
        integer, dimension(nk, nx), intent(out) :: kpol_ind
        
        integer :: x_c, k_c, kp_c
        real(kind=8), dimension(nk, nk) :: RHS
        real(kind=8), dimension(nk) :: EV_x, profit_x, kprime_vec
        real(kind=8) :: max_val
        integer :: max_ind
        real(kind=8) :: kprime_val, k_today_val, adj_val, rhs_val
        
        kprime_vec = k_grid
        
        ! 进行最大化（使用OpenMP并行化）
        !$omp parallel do private(x_c, EV_x, profit_x, kp_c, k_c, kprime_val, k_today_val, &
        !$omp& max_val, max_ind, adj_val)
        do x_c = 1, nx
            EV_x = EV(:, x_c)
            profit_x = profit_mat(:, x_c)
            
            ! 构建RHS矩阵 (nk, nk)
            do kp_c = 1, nk
                kprime_val = kprime_vec(kp_c)
                do k_c = 1, nk
                    k_today_val = k_grid(k_c)
                    ! 计算调整成本（内联，避免函数调用开销）
                    adj_val = kprime_val - (1.0d0 - delta) * k_today_val
                    if (kprime_val < (1.0d0 - delta) * k_today_val) then
                        adj_val = theta * adj_val
                    end if
                    ! 构建RHS
                    RHS(kp_c, k_c) = profit_x(kp_c) - adj_val + &
                              q * (psi * theta * (1.0d0 - delta) * kprime_val + &
                                   (1.0d0 - psi) * EV_x(kp_c))
                end do
            end do
            
            ! 找到最大值及其索引 (沿着第0维，即行方向)
            do k_c = 1, nk
                max_val = RHS(1, k_c)
                max_ind = 1
                do kp_c = 2, nk
                    if (RHS(kp_c, k_c) > max_val) then
                        max_val = RHS(kp_c, k_c)
                        max_ind = kp_c
                    end if
                end do
                V2(k_c, x_c) = max_val
                kpol_ind(k_c, x_c) = max_ind - 1  ! Python索引从0开始
            end do
        end do
        !$omp end parallel do
    end subroutine sub_V1_onestep_fortran_fast

! ============================================================
! 有约束企业VFI: sub_vfi_onestep (部分步骤)
! ============================================================

    subroutine step2_liquidation(val_c, val0_c, profit_mat, k_grid, b_grid, theta, delta, nk, nb, nx)
        ! STEP 2 - 施加清算，方程(24)
        integer, intent(in) :: nk, nb, nx
        real(kind=8), dimension(nk, nb, nx), intent(in) :: val_c
        real(kind=8), dimension(nk, nb, nx), intent(out) :: val0_c
        real(kind=8), dimension(nk, nx), intent(in) :: profit_mat
        real(kind=8), dimension(nk), intent(in) :: k_grid
        real(kind=8), dimension(nk, nb), intent(in) :: b_grid
        real(kind=8), intent(in) :: theta, delta
        
        integer :: k_c, b_c, x_c
        real(kind=8) :: k_val, b_val, profit_val, liq_val
        
        do x_c = 1, nx
            do b_c = 1, nb
                do k_c = 1, nk
                    k_val = k_grid(k_c)
                    b_val = b_grid(k_c, b_c)
                    profit_val = profit_mat(k_c, x_c)
                    liq_val = theta * (1.0d0 - delta) * k_val - b_val
                    
                    if (profit_val - b_val + theta * (1.0d0 - delta) * k_val < 0.0d0 .or. &
                        val_c(k_c, b_c, x_c) < liq_val) then
                        val0_c(k_c, b_c, x_c) = liq_val
                    else
                        val0_c(k_c, b_c, x_c) = val_c(k_c, b_c, x_c)
                    end if
                end do
            end do
        end do
    end subroutine step2_liquidation

    subroutine step3_constraint(val0_c, val0_u, b_hat, b_grid, val0, is_c, nk, nb, nx)
        ! STEP 3 - 执行方程(23)
        integer, intent(in) :: nk, nb, nx
        real(kind=8), dimension(nk, nb, nx), intent(in) :: val0_c, val0_u
        real(kind=8), dimension(nk, nx), intent(in) :: b_hat
        real(kind=8), dimension(nk, nb), intent(in) :: b_grid
        real(kind=8), dimension(nk, nb, nx), intent(out) :: val0
        integer, dimension(nk, nb, nx), intent(out) :: is_c
        
        integer :: k_c, b_c, x_c
        real(kind=8) :: b_val
        
        do x_c = 1, nx
            do b_c = 1, nb
                do k_c = 1, nk
                    b_val = b_grid(k_c, b_c)
                    if (b_val <= b_hat(k_c, x_c)) then
                        val0(k_c, b_c, x_c) = val0_u(k_c, b_c, x_c)
                        is_c(k_c, b_c, x_c) = 0
                    else
                        val0(k_c, b_c, x_c) = val0_c(k_c, b_c, x_c)
                        is_c(k_c, b_c, x_c) = 1
                    end if
                end do
            end do
        end do
    end subroutine step3_constraint

! ============================================================
! B_hat计算: sub_Bhat_onestep
! ============================================================

    subroutine sub_Bhat_onestep_fortran(B_hat, pol_kp_unc, profit_mat, x_tilde_val, k_grid, x_grid, &
                                        q, theta, delta, lambda_val, B_hat_new, pol_bp_unc, nk, nx)
        ! 找到B_hat(k,x)，与非负股息一致的最高债务水平
        integer, intent(in) :: nk, nx
        real(kind=8), dimension(nk, nx), intent(in) :: B_hat, pol_kp_unc, profit_mat
        real(kind=8), dimension(nk), intent(in) :: x_tilde_val, k_grid
        real(kind=8), dimension(nx), intent(in) :: x_grid
        real(kind=8), intent(in) :: q, theta, delta, lambda_val
        real(kind=8), dimension(nk, nx), intent(out) :: B_hat_new, pol_bp_unc
        
        integer :: x_c, k_c, kp_c, xp_c
        real(kind=8), dimension(nk) :: kp_val, B_hat_interp, x_cut
        real(kind=8), dimension(nk, nx) :: B_hat_interp_mat
        real(kind=8) :: k_min, k_max, kp_clipped, min_b_hat
        logical, dimension(nk, nx) :: viable_x
        
        k_min = k_grid(1)
        k_max = k_grid(nk)
        
        do x_c = 1, nx
            ! 裁剪kp到有效范围
            do k_c = 1, nk
                kp_clipped = max(k_min, min(k_max, pol_kp_unc(k_c, x_c)))
                kp_val(k_c) = kp_clipped
            end do
            
            ! 插值B_hat和x_tilde_val
            do k_c = 1, nk
                B_hat_interp(k_c) = myinterp1_fortran(k_grid, B_hat(:, x_c), nk, kp_val(k_c))
                x_cut(k_c) = myinterp1_fortran(k_grid, x_tilde_val, nk, kp_val(k_c))
            end do
            
            ! 找到可行的x
            do k_c = 1, nk
                do xp_c = 1, nx
                    viable_x(k_c, xp_c) = (x_grid(xp_c) >= x_cut(k_c))
                end do
            end do
            
            ! 计算pol_bp_unc
            do k_c = 1, nk
                ! 插值B_hat到所有x'
                do xp_c = 1, nx
                    B_hat_interp_mat(k_c, xp_c) = myinterp1_fortran(k_grid, B_hat(:, xp_c), nk, kp_val(k_c))
                    if (.not. viable_x(k_c, xp_c)) then
                        B_hat_interp_mat(k_c, xp_c) = huge(1.0d0)  ! NaN的替代
                    end if
                end do
                
                ! 找到最小值
                min_b_hat = B_hat_interp_mat(k_c, 1)
                do xp_c = 2, nx
                    if (B_hat_interp_mat(k_c, xp_c) < min_b_hat) then
                        min_b_hat = B_hat_interp_mat(k_c, xp_c)
                    end if
                end do
                
                pol_bp_unc(k_c, x_c) = min(lambda_val * kp_val(k_c), min_b_hat)
                
                ! 处理NaN（huge值）
                if (pol_bp_unc(k_c, x_c) > 1.0d10) then
                    pol_bp_unc(k_c, x_c) = lambda_val * pol_kp_unc(k_c, x_c)
                end if
            end do
        end do
        
        ! 计算B_hat_new
        do x_c = 1, nx
            do k_c = 1, nk
                kp_clipped = max(k_min, min(k_max, pol_kp_unc(k_c, x_c)))
                B_hat_new(k_c, x_c) = profit_mat(k_c, x_c) + q * pol_bp_unc(k_c, x_c) - &
                                      adjcost_scal_fortran(kp_clipped, k_grid(k_c), theta, delta)
            end do
        end do
    end subroutine sub_Bhat_onestep_fortran

! ============================================================
! 分布更新: sub_mu_onestep
! ============================================================

    subroutine sub_mu_onestep_fortran(mu, phi_dist, pol_kp_ind, pol_exit, pol_entry, &
                                     left_loc_arr, omega_arr, pi_x, mass, psi, &
                                     mu1, nk, nb, nx)
        ! 对分布mu^0进行一步算子操作
        integer, intent(in) :: nk, nb, nx
        real(kind=8), dimension(nk, nb, nx), intent(in) :: mu, phi_dist
        integer, dimension(nk, nb, nx), intent(in) :: pol_kp_ind, left_loc_arr
        real(kind=8), dimension(nk, nb, nx), intent(in) :: pol_exit, pol_entry, omega_arr
        real(kind=8), dimension(nx, nx), intent(in) :: pi_x
        real(kind=8), intent(in) :: mass, psi
        real(kind=8), dimension(nk, nb, nx), intent(out) :: mu1
        
        integer :: x_c, b_c, k_c, xp_c
        integer :: knext_ind, left_loc
        real(kind=8) :: dexit, entry, omega
        real(kind=8), dimension(nb, nx) :: temp
        
        mu1 = 0.0d0
        
        ! 更新分布
        do x_c = 1, nx
            do b_c = 1, nb
                do k_c = 1, nk
                    dexit = psi + (1.0d0 - psi) * pol_exit(k_c, b_c, x_c)
                    entry = pol_entry(k_c, b_c, x_c)
                    knext_ind = pol_kp_ind(k_c, b_c, x_c) + 1  ! Python索引转Fortran索引
                    left_loc = left_loc_arr(k_c, b_c, x_c) + 1
                    omega = omega_arr(k_c, b_c, x_c)
                    
                    ! 确保索引在有效范围内
                    knext_ind = max(1, min(nk, knext_ind))
                    left_loc = max(1, min(nb - 1, left_loc))
                    
                    ! 更新分布
                    mu1(knext_ind, left_loc, x_c) = mu1(knext_ind, left_loc, x_c) + &
                        omega * (1.0d0 - dexit) * mu(k_c, b_c, x_c) + &
                        omega * mass * entry * phi_dist(k_c, b_c, x_c)
                    
                    if (left_loc + 1 <= nb) then
                        mu1(knext_ind, left_loc + 1, x_c) = mu1(knext_ind, left_loc + 1, x_c) + &
                            (1.0d0 - omega) * (1.0d0 - dexit) * mu(k_c, b_c, x_c) + &
                            (1.0d0 - omega) * mass * entry * phi_dist(k_c, b_c, x_c)
                    end if
                end do
            end do
        end do
        
        ! 矩阵乘法: mu1(k',b',x)*pi(x,x')==> mu1(k',b',x')
        do k_c = 1, nk
            temp = mu1(k_c, :, :)
            mu1(k_c, :, :) = 0.0d0
            do xp_c = 1, nx
                do x_c = 1, nx
                    mu1(k_c, :, xp_c) = mu1(k_c, :, xp_c) + temp(:, x_c) * pi_x(x_c, xp_c)
                end do
            end do
        end do
    end subroutine sub_mu_onestep_fortran

end module vfi_core
