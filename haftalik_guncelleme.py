"""JARVIS weekly feature discovery report."""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from groq import Groq, GroqError

from jarvis_logging import get_logger

logger = get_logger("weekly_update")
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

CURRENT_FEATURES = """
- Wake-word activation and voice command recognition
- Edge TTS voice responses with provider selection
- Desktop app launching and browser automation
- Screenshot capture, keyboard, mouse, and clipboard actions
- Spotify playback, search, and volume control
- Groq command routing with local LLM fallback planning
- First-run onboarding, settings, health, memory, plugin, logs, and README UI
- Offline speech recognition fallback when a local Vosk model is available
- Memory health scoring, pruning, and activity summaries
- Runtime events, feature quality registry, release signing, and plugin trust validation
"""


def scan_github() -> list[dict]:
    """Scan GitHub for popular Python assistant projects."""

    logger.info("Weekly report scan started.")
    searches = [
        "python voice assistant jarvis",
        "python AI desktop automation",
        "python speech recognition assistant",
        "python computer vision automation",
        "python smart home assistant",
    ]
    projects: list[dict] = []
    headers = {"Accept": "application/vnd.github.v3+json"}

    for search in searches:
        try:
            response = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": f"{search} language:python", "sort": "stars", "order": "desc", "per_page": 10},
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                for repo in response.json().get("items", []):
                    if repo.get("description"):
                        projects.append(
                            {
                                "name": repo["name"],
                                "description": repo.get("description", ""),
                                "stars": repo["stargazers_count"],
                                "url": repo["html_url"],
                                "topics": repo.get("topics", []),
                            }
                        )
        except (requests.RequestException, ValueError) as exc:
            logger.exception("GitHub scan error: %s", exc)

    unique = {project["name"]: project for project in projects}
    return sorted(unique.values(), key=lambda item: item["stars"], reverse=True)[:50]


def analyze_with_groq(projects: list[dict]) -> str:
    """Send project data to Groq and return practical feature suggestions."""

    if client is None:
        logger.warning("Weekly report skipped: GROQ_API_KEY is missing.")
        return "Groq analysis skipped because GROQ_API_KEY is missing in your .env file."
    project_text = "\n".join([f"- {project['name']} ({project['stars']:,} stars): {project['description']}" for project in projects[:15]])

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"""
You are an expert JARVIS voice assistant developer.

JARVIS CURRENT FEATURES:
{CURRENT_FEATURES}

SCANNED GITHUB PROJECTS:
{project_text}

Suggest 6 new features that are not already in JARVIS.
For each feature provide:
1. Feature name
2. What it does in 2-3 sentences
3. Example voice command
4. Which Python library to use
5. Difficulty: Easy / Medium / Hard
6. Priority: High / Medium / Low

Write in English. Be practical and realistic.
""",
                }
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        return response.choices[0].message.content or "Groq returned an empty analysis."
    except (GroqError, AttributeError) as exc:
        logger.exception("Weekly report Groq error: %s", exc)
        return f"Groq error: {exc}"


def _desktop_path() -> Path:
    user_profile = Path(os.environ.get("USERPROFILE", ""))
    one_drive = user_profile / "OneDrive" / "Desktop"
    return one_drive if one_drive.exists() else user_profile / "Desktop"


def save_report(content: str, projects: list[dict]) -> Path:
    """Save the weekly feature report to the Desktop."""

    report_date = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = _desktop_path() / f"jarvis_report_{report_date}.txt"

    with file_path.open("w", encoding="utf-8") as handle:
        handle.write("=" * 60 + "\n")
        handle.write(f"  JARVIS WEEKLY FEATURE REPORT - {report_date}\n")
        handle.write("=" * 60 + "\n\n")
        handle.write(f"PROJECTS SCANNED: {len(projects)}\n\n")
        handle.write("TOP PROJECTS FOUND:\n")
        handle.write("-" * 40 + "\n")
        for project in projects[:12]:
            handle.write(f"  {project['stars']:>7,} stars - {project['name']}\n")
            handle.write(f"  {project['description']}\n")
            handle.write(f"  {project['url']}\n\n")
        handle.write("\n" + "=" * 60 + "\n")
        handle.write("SUGGESTED NEW FEATURES FOR JARVIS:\n")
        handle.write("=" * 60 + "\n\n")
        handle.write(content)
        handle.write("\n\n" + "=" * 60 + "\n")
        handle.write("Use this report to choose the next roadmap items.\n")
        handle.write("=" * 60 + "\n")

    logger.info("Weekly report saved to %s", file_path)
    return file_path


def main() -> int:
    print("JARVIS weekly update starting...")
    projects = scan_github()
    print(f"{len(projects)} projects found.")
    analysis = analyze_with_groq(projects)
    file_path = save_report(analysis, projects)
    print(f"Done. Report saved: {file_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
