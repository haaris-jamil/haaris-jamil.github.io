"""Publish the exact Pages artifact returned by upload-pages-artifact.

Avoid rediscovering an already-uploaded artifact through the intermittently
empty name-listing service. Use the same Pages/OIDC APIs as deploy-pages.
"""
import json
import os
import signal
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"GitHub API returned HTTP {status}")


def request_json(url, token, payload=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "portfolio-pages-publisher",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(url, data=data, headers=headers), timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except HTTPError as error:
        # Never include request headers, OIDC URLs or response token bodies.
        raise ApiError(error.code) from None


FINAL_FAILURES = {
    "deployment_failed", "deployment_perms_error", "deployment_content_failed",
    "deployment_cancelled", "deployment_lost",
}
TEMPORARY_HTTP = {404, 429, 500, 502, 503, 504}


def publish(env, *, request=request_json, sleep=time.sleep,
            clock=time.monotonic, timeout=600):
    artifact = env["PAGES_ARTIFACT_ID"]
    if not str(artifact).isdigit() or int(artifact) <= 0:
        raise ValueError("The upload did not return a valid Pages artifact ID")
    repository = env["GITHUB_REPOSITORY"]
    if len(repository.split("/")) != 2:
        raise ValueError("Invalid repository name")
    token = env["GITHUB_TOKEN"]
    oidc = request(env["ACTIONS_ID_TOKEN_REQUEST_URL"],
                   env["ACTIONS_ID_TOKEN_REQUEST_TOKEN"])
    identity = oidc.get("value")
    if not identity:
        raise RuntimeError("GitHub did not return the Pages identity token")
    base = env.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    endpoint = f"{base}/repos/{repository}/pages/deployments"
    payload = {"artifact_id": int(artifact),
               "pages_build_version": env["GITHUB_SHA"],
               "oidc_token": identity}

    # A newly uploaded artifact may briefly be unavailable to the Pages API.
    # Only retry explicit rejection responses; a lost POST response is ambiguous.
    for attempt in range(5):
        try:
            created = request(endpoint, token, payload)
            break
        except ApiError as error:
            if error.status not in {404, 409, 429} or attempt == 4:
                raise
            delay = min(5 * 2 ** attempt, 30)
            print(f"Pages is not ready (HTTP {error.status}); retrying in {delay}s.", flush=True)
            sleep(delay)

    deployment_id = created.get("id") or created.get("status_url", "").rstrip("/").split("/")[-1]
    if not deployment_id:
        raise RuntimeError("GitHub did not return a Pages deployment ID")
    status_url = endpoint + "/" + quote(str(deployment_id), safe="")
    page_url = created.get("page_url", "")
    started = clock()
    last_status = None
    print(f"Publishing uploaded artifact {artifact} as deployment {deployment_id}.", flush=True)
    try:
        while clock() - started < timeout:
            try:
                result = request(status_url, token)
            except ApiError as error:
                if error.status not in TEMPORARY_HTTP:
                    raise
                print(f"Temporary Pages status error (HTTP {error.status}); checking again.", flush=True)
                sleep(5)
                continue
            status = result.get("status", "unknown_status")
            if status == "succeed":
                print("GitHub Pages publication succeeded.", flush=True)
                return page_url or result.get("page_url", "")
            if status in FINAL_FAILURES:
                raise RuntimeError(f"GitHub Pages reported {status}")
            if status != last_status:
                print(f"Pages status: {status}", flush=True)
                last_status = status
            sleep(5)
        raise TimeoutError("GitHub Pages did not finish within ten minutes")
    except BaseException:
        try:
            request(status_url + "/cancel", token, {})
        except Exception:
            print("Could not confirm cancellation of the unfinished deployment.", flush=True)
        raise


def main():
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt("Pages job was cancelled")
    signal.signal(signal.SIGTERM, interrupted)
    try:
        page_url = publish(os.environ)
        if not page_url.startswith("https://") or "\n" in page_url or "\r" in page_url:
            raise RuntimeError("GitHub did not return a valid published website URL")
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"page_url={page_url}\n")
    except (Exception, KeyboardInterrupt) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
