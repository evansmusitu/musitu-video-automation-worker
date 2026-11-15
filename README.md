# MUSITU Video Automation Worker

Python and Playwright worker for **authorized playback testing** and **read-only public-site audits**. This is an initial tested version, not a reward-earning bot.

## Commands

Requirements: Python 3.11+, Chromium or Playwright Chromium, ffmpeg.

```bash
pip install -r requirements.txt
python -m playwright install chromium
python worker.py local-playback --seconds 1.5 --output reports/local.json
python worker.py audit-stremio --output reports/stremio-public.json
python worker.py record-manual-balance --before 0 --after 0 --output reports/manual.json
python -m pytest -q
```

- `local-playback`: Generate an original local test video and use Chromium to verify that media time advances; never contact a paid-view service.
- `audit-stremio`: Read only the public homepage `https://stremio.cx/`, without logging in, watching videos or interacting with reward features. Network or access failures are reported as **unverified**, never success.
- `record-manual-balance`: Record figures you provide for comparison; no payout proof is claimed.

**A displayed balance is not evidence of cash received.** Only confirmation of money actually arriving at the payment provider after a legitimate, permitted withdrawal can support a payout claim.

## Limits

No artificial reward views, fake engagement, referrals, account registration, withdrawal circumvention, or anti-bot evasion. The public website advertises up to $60/hour, but payout reliability is unverified. Do not send identification, deposits, or paid verification fees to an untrusted site.

The local test passed 3 tests on 15 November 2026. Real-site browser navigation was blocked in the test environment, so `audit-stremio` could not be completed there.
