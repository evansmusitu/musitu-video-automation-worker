"""Authorized local playback test and read-only homepage audit.

Never generates artificial rewarded views or attempts payments or withdrawals.
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE_HOME = "https://stremio.cx/"


def chromium_kwargs():
    binary = shutil.which("chromium") or shutil.which("chromium-browser")
    return {"executable_path": binary} if binary else {}


def write_report(data, output=None):
    rendered = json.dumps(data, indent=2, sort_keys=True)
    print(rendered)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")


def test_local_playback(seconds=1.5):
    """Generate an owned test video, play it locally and measure progress."""
    if not 0.5 <= seconds <= 4:
        raise ValueError("seconds must be between 0.5 and 4")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    with tempfile.TemporaryDirectory(prefix="musitu-playback-") as temp:
        video_file = Path(temp) / "sample.webm"
        subprocess.run([
            ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi",
            "-i", "color=c=blue:s=160x90:r=15", "-t", "5", "-an",
            "-c:v", "libvpx", "-b:v", "75k", str(video_file),
        ], check=True, capture_output=True, text=True, timeout=30)
        data = base64.b64encode(video_file.read_bytes()).decode("ascii")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--no-sandbox"], **chromium_kwargs()
            )
            try:
                page = browser.new_page()
                page.set_content(
                    '<!doctype html><html lang="en"><title>Owned fixture</title>'
                    f'<video id="demo" src="data:video/webm;base64,{data}" '
                    'muted playsinline controls preload="auto"></video></html>'
                )
                video = page.locator("#demo")
                video.evaluate("v => v.play()")
                before = float(video.evaluate("v => v.currentTime"))
                page.wait_for_timeout(int(seconds * 1000))
                after = float(video.evaluate("v => v.currentTime"))
                progression = round(after - before, 3)
                return {
                    "mode": "local_authorized_video_playback_test",
                    "result": "pass" if progression >= 0.5 else "fail",
                    "elapsed_media_seconds": progression,
                    "played_own_fixture": True,
                    "third_party_paid_views_generated": 0,
                    "real_site_rewards_verified": False,
                }
            finally:
                browser.close()


def audit_public_homepage(timeout_ms=25000):
    """Read only the public homepage; no videos, sign-in or interactions."""
    report = {
        "mode": "read_only_public_homepage_audit",
        "url": SITE_HOME,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "rewards_earned_or_paid": "not_tested",
        "note": "Marketing copy or on-screen balances cannot prove a payout.",
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--no-sandbox"], **chromium_kwargs()
            )
            try:
                page = browser.new_page(service_workers="block")
                response = page.goto(
                    SITE_HOME, wait_until="domcontentloaded", timeout=timeout_ms
                )
                text = page.locator("body").inner_text(timeout=10000)
                report.update({
                    "result": "public_page_readable",
                    "http_status": response.status if response else None,
                    "title": page.title(),
                    "advertises_60_dollars_per_hour": "$60 per hour" in text,
                    "advertises_1_dollar_per_minute":
                        "1.00/min" in text or "$1 per minute" in text,
                    "has_sign_in_link":
                        page.get_by_role("link", name="Sign in").count() > 0,
                })
            finally:
                browser.close()
    except Exception as exc:
        report.update({
            "result": "unverified_due_to_error",
            "error": f"{type(exc).__name__}: {exc}"[:1000],
        })
    return report


def manual_balance_observation(before, after):
    """Compare balances reported by a user, not verified by this script."""
    if before < 0 or after < 0:
        raise ValueError("Displayed balances cannot be negative")
    return {
        "mode": "manual_balance_observation",
        "before_usd_user_reported": before,
        "after_usd_user_reported": after,
        "displayed_balance_change_usd": round(after - before, 2),
        "payout_independently_verified": False,
        "warning": "On-screen balance is not proof of funds received.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    local = sub.add_parser("local-playback")
    local.add_argument("--seconds", type=float, default=1.5)
    local.add_argument("--output", type=Path)
    audit = sub.add_parser("audit-stremio")
    audit.add_argument("--output", type=Path)
    balance = sub.add_parser("record-manual-balance")
    balance.add_argument("--before", type=float, required=True)
    balance.add_argument("--after", type=float, required=True)
    balance.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "local-playback":
        report = test_local_playback(args.seconds)
    elif args.command == "audit-stremio":
        report = audit_public_homepage()
    else:
        report = manual_balance_observation(args.before, args.after)
    write_report(report, args.output)
    return 1 if report.get("result") in ("fail", "unverified_due_to_error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
