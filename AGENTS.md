# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a Python port of the MATLAB code for the paper "Rescue Policies for Small Businesses During the Covid-19 Recession" (Di Nola, Kaas, Wang 2023). It performs heterogeneous firm model computations: steady state, transition dynamics, calibration, and welfare analysis. The `china_dsge/` sub-directory contains a separate MATLAB-only DSGE model that is **not runnable** in this environment.

### Running the application

- Entry point: `python main.py` (uses Numba JIT; see `README.md`).
- A full steady-state run (default `do_calib = 0`) takes 30–80 minutes with the production grid (60×80×100). Set relaxed tolerances in `main.py` (already present as `par['tol_*'] = 0.01`) for quick smoke tests.
- There is a pre-existing computation bug in `fun_steady_state.py` → `fun_fixcost` that causes `main.py` to error during steady-state computation. This is **not** an environment issue.

### Dependencies

`pip install -r requirements.txt` — installs numpy, scipy, matplotlib, pandas, mpmath, numba. No other system dependencies are required for the default (Numba) path.

### Testing

- No formal test framework (pytest/unittest) is configured.
- Ad-hoc test scripts exist in the repo root: `test_tolerance.py`, `test_max_direction.py`, `test_numba_required.py`, `test_pol_kp_unc_calculation.py`, `test_calibration.py`, `quick_test.py`, `quick_test_main.py`.
- Run them individually with `python <script>.py`.
- Syntax-check all 142 `.py` files: `python -c "import py_compile, os; [py_compile.compile(os.path.join(r,f), doraise=True) for r,d,fs in os.walk('.') if '.git' not in r for f in fs if f.endswith('.py')]"`.

### Linting

No linting tool (flake8/pylint/ruff) is configured. There is no `pyproject.toml`, `setup.cfg`, or `.flake8`.

### Optional Fortran acceleration

Install `gfortran`, then run `python fortran/setup_fortran.py` to build the Fortran VFI module for ~10× speedup. Use `python main_fortran.py` instead of `main.py`. See `FORTRAN_SETUP.md`.
