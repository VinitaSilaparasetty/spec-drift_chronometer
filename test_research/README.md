# Spec-Drift Chronometer — Research Test Suite

This folder contains the real-world test suite used to generate empirical data
for the IEEE Software paper submission.

## What This Tests

1. **Real drift detection**: Measures actual semantic deviation between git commits
   and the human-authored specification vault in `.kiro/steering/`

2. **Real justification evaluation**: Tests the Justification Gate with three
   justification quality levels evaluated by real LLM inference

## How to Run

### Prerequisites
- Backend running: `uvicorn backend.main:app --port 8000` from repository root
- Python dependencies: `pip install -r requirements.txt`
- API key for chosen LLM (passed as environment variable, never stored in files)

### Run with Gemini (free tier)
```
GEMINI_API_KEY=your-key WARDEN_LLM=gemini python run_tests.py --llm gemini
```

### Run with Hugging Face Mistral (free tier)
```
HF_API_KEY=your-token WARDEN_LLM=huggingface python run_tests.py --llm huggingface
```

## Security
API keys are never stored in files. Pass them as environment variables only.
The results/ folder is gitignored to prevent accidental commits of test data
containing sensitive information.

## Results
Results are saved to results/ after each test run. Compare results across
LLMs by examining the justification_results files side by side.

## Relationship to IEEE Paper
The drift_results tables provide the concrete examples requested by the
IEEE Software editor. The justification_results tables demonstrate the
rubber stamp detection failure mode and cross-LLM consistency.
