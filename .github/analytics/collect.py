"""Collect aggregate GoatCounter statistics and save only an encrypted report."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://marcogpalladino.goatcounter.com"


def get(endpoint, params):
    token = os.environ.get("GOATCOUNTER_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing GOATCOUNTER_API_TOKEN repository secret")
    request = Request(BASE + "/api/v0/stats/" + endpoint + "?" + urlencode(params),
                      headers={"Authorization": "Bearer " + token,
                               "Content-Type": "application/json"})
    for attempt in range(4):
        time.sleep(0.35)
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
            if not isinstance(data, dict) or "error" in data or "errors" in data:
                raise RuntimeError("Unexpected GoatCounter response")
            return data
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            # Never put response bodies or request headers in public Actions logs.
            raise RuntimeError("GoatCounter HTTP " + str(exc.code)) from None
        except (URLError, TimeoutError):
            if attempt == 3:
                raise RuntimeError("GoatCounter connection failed") from None


def period(start, end):
    params = {"start": start.isoformat(), "end": end.isoformat()}
    totals = get("total", params)
    hits, seen = [], set()
    while True:
        query = {**params, "limit": 100}
        if seen:
            query["exclude_paths"] = ",".join(str(x) for x in sorted(seen))
        page = get("hits", query)
        batch = page.get("hits") or []
        ids = {hit["path_id"] for hit in batch}
        if ids & seen:
            raise RuntimeError("Unexpected repeated page in GoatCounter pagination")
        hits.extend(batch)
        seen.update(ids)
        if not page.get("more"):
            break
        if not ids or len(seen) > 10000:
            raise RuntimeError("GoatCounter pagination did not finish")
    dimensions = {}
    for dimension in ("locations", "toprefs"):
        rows, offset = [], 0
        while True:
            page = get(dimension, {**params, "limit": 100, "offset": offset})
            batch = page.get("stats") or []
            rows.extend(batch)
            if not page.get("more"):
                break
            if not batch or offset > 10000:
                raise RuntimeError("GoatCounter pagination did not finish")
            offset += len(batch)
        dimensions[dimension] = rows
    return {**params, "totals": totals, "hits": hits, **dimensions}


def main():
    now = datetime.now(timezone.utc)
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    middle = end - timedelta(days=14)
    report = {
        "schema_version": 1,
        "site": BASE,
        "generated_at": now.isoformat(),
        "timezone": "UTC",
        "tracking_started": "2026-09-07",
        "notes": [
            "Raw aggregate API metrics: preserve their meaning; do not sum per-page counts as site-wide unique people.",
            "Events are clicks, not confirmed downloads. Separate event=true rows from page views.",
            "Tracking only began on 2026-09-07; earlier periods are incomplete, not evidence of zero historical traffic.",
            "The two query windows each span 14 calendar days and exclude the current partial day.",
        ],
        "current": period(middle, end),
        "previous": period(middle - timedelta(days=14), middle),
    }
    destination = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "goatcounter-report.cms"
    certificate = Path(__file__).with_name("report-recipient.pem")
    subprocess.run([
        "openssl", "cms", "-encrypt", "-binary", "-aes-256-gcm",
        "-outform", "DER", "-out", str(destination), str(certificate),
    ], input=json.dumps(report, ensure_ascii=False).encode(), check=True,
       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print("Encrypted analytics report created successfully.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("Analytics collection failed; no report was published.", file=sys.stderr)
        sys.exit(1)
