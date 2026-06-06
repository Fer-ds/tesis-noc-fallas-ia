# Tabla top-k Sprint 7 HPO

| rank | método | trial | F1 mean±std | precision | recall | AP | threshold | params resumidos |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | random_search | 8 | 0.4986±0.0461 | 0.3333 | 1.0000 | 0.4395 | 0.230 | lr=0.078, depth=2, leaf=59, n=60, ccp=1.3e-04 |
| 2 | bayesian_gp_ucb | 6 | 0.4986±0.0461 | 0.3333 | 1.0000 | 0.4348 | 0.207 | lr=0.046, depth=2, leaf=45, n=89, ccp=2.6e-06 |
| 3 | bayesian_gp_ucb | 10 | 0.4986±0.0461 | 0.3333 | 1.0000 | 0.4347 | 0.198 | lr=0.034, depth=3, leaf=40, n=78, ccp=1.6e-04 |
| 4 | bayesian_gp_ucb | 1 | 0.4986±0.0461 | 0.3333 | 1.0000 | 0.4281 | 0.219 | lr=0.085, depth=1, leaf=44, n=173, ccp=1.3e-05 |
| 5 | random_search | 10 | 0.4986±0.0461 | 0.3333 | 1.0000 | 0.4202 | 0.206 | lr=0.016, depth=2, leaf=39, n=127, ccp=1.4e-03 |
| 6 | bayesian_gp_ucb | 3 | 0.4986±0.0461 | 0.3333 | 1.0000 | 0.4171 | 0.315 | lr=0.046, depth=3, leaf=61, n=91, ccp=2.2e-03 |
| 7 | bayesian_gp_ucb | 9 | 0.4982±0.0456 | 0.3333 | 0.9984 | 0.4398 | 0.180 | lr=0.028, depth=4, leaf=16, n=115, ccp=3.1e-05 |
| 8 | random_search | 5 | 0.4980±0.0134 | 0.3668 | 0.7969 | 0.4472 | 0.389 | lr=0.166, depth=3, leaf=37, n=171, ccp=5.5e-05 |
| 9 | bayesian_gp_ucb | 11 | 0.4974±0.0446 | 0.3329 | 0.9956 | 0.4319 | 0.262 | lr=0.125, depth=2, leaf=30, n=110, ccp=9.1e-04 |
| 10 | bayesian_gp_ucb | 4 | 0.4963±0.0143 | 0.3779 | 0.7327 | 0.4376 | 0.456 | lr=0.063, depth=3, leaf=20, n=84, ccp=4.6e-04 |
