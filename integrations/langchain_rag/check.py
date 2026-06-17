"""
Pre-flight check for the Spec-Drift Chronometer LangChain integration.

Run this before rag_chatbot.py or langgraph_example.py to confirm that
your environment, API key, and Warden Engine are all ready.

Usage:
    python check.py
"""

from __future__ import annotations
import os
import sys

PASS = "  [PASS]"
FAIL = "  [FAIL]"
WARN = "  [WARN]"


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = PASS if ok else FAIL
    print(f"{status}  {label}" + (f"\n         {detail}" if detail else ""))
    return ok


def main() -> None:
    print()
    print("Spec-Drift Chronometer — Integration Pre-flight Check")
    print("=" * 54)
    print()

    all_ok = True

    # ------------------------------------------------------------------
    # 1. .env file
    # ------------------------------------------------------------------
    print("[ Environment ]")
    env_exists = os.path.exists(".env")
    all_ok &= check(".env file present", env_exists,
                    "Run: cp .env.example .env  then fill in OPENAI_API_KEY")

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    key_set = bool(api_key) and api_key != "your_key_here"
    all_ok &= check("OPENAI_API_KEY is set", key_set,
                    "Open .env and set OPENAI_API_KEY=sk-...")
    print()

    # ------------------------------------------------------------------
    # 2. Required packages
    # ------------------------------------------------------------------
    print("[ Dependencies ]")
    packages = {
        "langchain_core": "langchain-core",
        "langchain_community": "langchain-community",
        "langchain_openai": "langchain-openai",
        "langgraph": "langgraph",
        "faiss": "faiss-cpu",
        "requests": "requests",
    }
    for module, pip_name in packages.items():
        try:
            __import__(module)
            all_ok &= check(pip_name, True)
        except ImportError:
            all_ok &= check(pip_name, False, f"Run: pip install {pip_name}")
    print()

    # ------------------------------------------------------------------
    # 3. OpenAI key validity — make the smallest possible API call
    # ------------------------------------------------------------------
    print("[ OpenAI API ]")
    if not key_set:
        print(f"{WARN}  Skipping API call — key not set")
    else:
        try:
            from openai import OpenAI, AuthenticationError, PermissionDeniedError
            client = OpenAI(api_key=api_key)
            # List models is the cheapest possible authenticated call
            client.models.list()
            all_ok &= check("API key is valid", True)

            # Verify gpt-4o-mini is accessible on this account
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Reply with the single word OK."}],
                    max_tokens=5,
                )
                reply = resp.choices[0].message.content.strip()
                all_ok &= check("gpt-4o-mini accessible", True, f'Response: "{reply}"')
            except PermissionDeniedError:
                all_ok &= check("gpt-4o-mini accessible", False,
                                "Your account cannot access gpt-4o-mini. "
                                "Edit rag_chatbot.py and change the model to one you have access to.")
            except Exception as exc:
                all_ok &= check("gpt-4o-mini accessible", False, str(exc))

        except AuthenticationError:
            all_ok &= check("API key is valid", False,
                            "Key was rejected by OpenAI. Check for typos or a revoked key.")
        except Exception as exc:
            all_ok &= check("API key is valid", False, str(exc))
    print()

    # ------------------------------------------------------------------
    # 4. Warden Engine reachability
    # ------------------------------------------------------------------
    print("[ Warden Engine ]")
    warden_url = os.environ.get("WARDEN_API_URL", "http://localhost:8000")
    try:
        import requests
        r = requests.get(f"{warden_url}/drift", timeout=4)
        r.raise_for_status()
        data = r.json()
        all_ok &= check(
            f"Warden reachable at {warden_url}",
            True,
            f"drift={data['drift']:.4f}  gate={data['gate']}  status={data['status']}",
        )
    except Exception as exc:
        # Warden unavailable is a warning, not a hard failure — the chatbot
        # degrades gracefully when skip_on_warden_unavailable=True
        print(f"{WARN}  Warden not reachable at {warden_url}")
        print(f"         {exc}")
        print(f"         Start it with: DEMO_MODE=true ./dev.sh  (from the repo root)")
        print(f"         The chatbot will still run but governance checks will be skipped.")
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    if all_ok:
        print("All checks passed. You are ready to run:")
        print("  python rag_chatbot.py")
        print("  python langgraph_example.py")
    else:
        print("One or more checks failed. Fix the issues above and re-run this script.")
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
