## Test Summary — mistral — 20260624_155613

### Test Configuration
- LLM Backend: mistral
- Model: mistral-small-latest
- Backend URL: http://localhost:8000
- Repository: /private/tmp/sdc_fresh_clone
- Drift Threshold: 0.0075

### Drift Detection Findings
Local drift scores were: LOW_DRIFT=0.5000, HIGH_DRIFT=0.7895, SPEC_VIOLATION=0.8421, NEUTRAL=0.8333. Local and backend scores agreed (within 0.001) on 0/4 commits. HIGH_DRIFT and SPEC_VIOLATION commits produced the highest local drift scores.

### Justification Evaluation Findings
Weak justifications were rejected 2/3 times, medium 3/3, and strong justifications were approved 3/3 times. Score differentiation across quality tiers is reported in justification_results_mistral.md.

### Cross-LLM Observations
To be completed after all LLM test sessions are run and results compared.

### Limitations Observed
The drift calculator compares token vocabularies against the spec vault; it does not perform semantic embedding comparison. Gate triggering depends on the backend's internal sample-diff cycle in demo mode, which may not always align with the test commit timing.
