## Drift Measurement Results — huggingface

| Commit Label | Description | New Tokens Introduced | Local Drift Score | Backend Drift Score | Agreement | Gate Triggered |
|---|---|---|---|---|---|---|
| LOW_DRIFT | governance comment using approved spec vocabulary | 89a906a, diff, index, logging, newline, null, research, temp, test | 0.500000 | 0.0012 | NO — delta: 0.4988 | no |
| HIGH_DRIFT | non-spec blockchain vocabulary introduced | af44fc9, blockchain, consensus, cryptographic, diff, distributed, index, merkle, newline, null… | 0.789474 | 0.0012 | NO — delta: 0.7883 | no |
| SPEC_VIOLATION | synchronous pattern contradicting async spec | 0ae9797, async, blocking, bypassing, database, diff, index, newline, null, operation… | 0.842105 | 0.0012 | NO — delta: 0.8409 | no |
| NEUTRAL | minimal vocabulary impact | 5176d9e, diff, index, minor, newline, null, research, temp, test, update | 0.833333 | 0.0012 | NO — delta: 0.8321 | no |
