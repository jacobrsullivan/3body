# WP4-MR-REPL-v1

This campaign independently regenerates the parabolic-Lagrange normal
variational equation from the declared reduced Newtonian Hamiltonian and
qualifies an exact non-Abelian differential-Galois certificate on the complete
finite positive-mass domain.

Lifecycle:

```bash
./validation-external/wp4-mr-repl-v1/run_qualification.sh test
./validation-external/wp4-mr-repl-v1/run_qualification.sh freeze
./validation-external/wp4-mr-repl-v1/run_qualification.sh execute
./validation-external/wp4-mr-repl-v1/run_qualification.sh finalize
./validation-external/wp4-mr-repl-v1/run_qualification.sh verify
```

`execute` requires the three hash-pinned PDFs named by the environment
variables in `run_qualification.sh`. The generic exact SymPy replay is
deliberately slow because it operates over
`Q(sqrt(3), i)(m1, m2)`.

