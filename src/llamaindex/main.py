"""
Main entry point for Opportunity & Visa Matcher.
Supports Streamlit web interface and CLI evaluation mode.
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()


def run_cli_demo(language: str = "en") -> None:
    """Run evaluation in CLI mode using sample documents."""
    is_ar = language.lower().startswith("ar")
    title = "مطابقة الفرص والتأشيرات" if is_ar else "Opportunity & Visa Matcher (CLI Mode)"
    print("=" * 60)
    print(title)
    print("=" * 60)

    from llamaindex.matcher import analyze_opportunity_and_visa

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_cv = os.path.join(base_dir, "sample_data", "sample_cv.pdf")
    sample_job = os.path.join(base_dir, "sample_data", "sample_opportunity.pdf")
    visa_url = os.getenv("VISA_RULES_URL", "https://en.wikipedia.org/wiki/Visa_policy_of_the_Schengen_Area")

    print(f"Candidate CV: {sample_cv}")
    print(f"Opportunity:  {sample_job}")
    print(f"Visa Rules:   {visa_url}")
    print("-" * 60)
    print("Processing documents and generating evaluation report...")

    try:
        report = analyze_opportunity_and_visa(
            cv_file_path=sample_cv,
            opportunity_file_path=sample_job,
            visa_url=visa_url,
            language=language,
        )
        print("\n" + "=" * 60)
        report_header = "تقرير التقييم:" if is_ar else "EVALUATION REPORT:"
        print(report_header)
        print("=" * 60)
        print(report)
        print("=" * 60)
    except Exception as error:
        print(f"\nError: {error}")


def run_web_app() -> None:
    """Launch the Streamlit web interface."""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])


def main() -> None:
    """Main entrypoint dispatcher."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage:")
        print("  uv run python -m llamaindex.main         # Launch Web Dashboard")
        print("  uv run python -m llamaindex.main --cli   # Run CLI Evaluation (English)")
        print("  uv run python -m llamaindex.main --cli --lang ar # Run CLI Evaluation (Arabic)")
        return

    if "--cli" in sys.argv:
        lang = "en"
        for i, arg in enumerate(sys.argv):
            if arg in ("--ar", "--arabic") or arg == "--lang=ar":
                lang = "ar"
                break
            elif arg == "--lang" and i + 1 < len(sys.argv):
                lang = sys.argv[i + 1]
                break
        run_cli_demo(language=lang)
    else:
        run_web_app()


if __name__ == "__main__":
    main()
