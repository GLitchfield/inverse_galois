\\ Official IGP24 MIXED discriminant (rules markdown, 2026-07-09): the grader's fallback when the
\\ full nfdisc times out is exactly nfdisc([f, 100000]) -- nfdisc with a partial-factorization bound
\\ B on poldisc (primes > B are handled without full certification). Matching this form makes our
\\ scoreability prediction faithful to the grader; the previous product-of-local-nfdisc form did not.
mixed_disc(f, B = 100000) = nfdisc([f, B]);
