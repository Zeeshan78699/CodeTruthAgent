"""
cceval_repo_fetch.py
CodeTruth Agent V3 — Phase 1 (CrossCodeEval real-repo evaluation), STAGE 1:
resolve + clone repositories at the specified commit, and report availability
BEFORE any CodeTruth evaluation. Transparency on the denominator is the point.

CrossCodeEval flattens repo identity into `owner-name-shortsha`, e.g.
`turboderp-exllama-a544085` or `datasig-ac-uk-RoughPy-fbd9016`. Both owner and
name can contain hyphens, so the split is AMBIGUOUS. We:
  1. peel the trailing `-<shortsha>` (commit),
  2. try every owner/name split of the remaining `a-b-c-...` against the GitHub
     API until one resolves to a real repo,
  3. shallow-clone and checkout the commit.
Every repo that cannot be resolved / cloned / checked-out is RECORDED, not
silently dropped. Output is an availability report:
  repos_total, resolved, clone_ok, commit_ok, and the per-repo status list.

No CodeTruth here — this stage only answers "can we get the code".
"""

import json
import os
import subprocess
import urllib.request
import urllib.error


GITHUB_API = "https://api.github.com/repos/{owner}/{name}"


def parse_repo_field(repo_field):
    """`owner-name-shortsha` -> (candidates, shortsha). candidates is the list of
    (owner, name) splits to try, longest-owner-first is arbitrary so we try all."""
    parts = repo_field.split("-")
    if len(parts) < 2:
        return [], None
    shortsha = parts[-1]
    body = parts[:-1]                      # owner+name tokens
    candidates = []
    for i in range(1, len(body)):          # split point between owner and name
        owner = "-".join(body[:i])
        name = "-".join(body[i:])
        candidates.append((owner, name))
    return candidates, shortsha


def resolve_on_github(candidates, token=None):
    """Return (owner, name, clone_url) for the first candidate GitHub confirms."""
    for owner, name in candidates:
        url = GITHUB_API.format(owner=owner, name=name)
        req = urllib.request.Request(url, headers={"User-Agent": "codetruth-cceval"})
        if token:
            req.add_header("Authorization", f"token {token}")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                return owner, name, data.get("clone_url")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):       # rate-limited: report, don't guess
                return None, None, "RATE_LIMITED"
            continue
        except Exception:
            continue
    return None, None, None


def clone_at_commit(clone_url, shortsha, dest):
    """Shallow clone + checkout the commit. Returns status dict."""
    if os.path.exists(dest):
        return {"clone_ok": True, "commit_ok": None, "note": "already present"}
    try:
        subprocess.run(["git", "init", "-q", dest], check=True)
        subprocess.run(["git", "-C", dest, "remote", "add", "origin", clone_url], check=True)
        # try to fetch just the commit (works on GitHub if allowReachableSHA);
        # fall back to a shallow default-branch clone then checkout.
        fetched = subprocess.run(
            ["git", "-C", dest, "fetch", "--depth", "1", "origin", shortsha],
            capture_output=True)
        if fetched.returncode == 0:
            co = subprocess.run(["git", "-C", dest, "checkout", "-q", "FETCH_HEAD"],
                                capture_output=True)
            return {"clone_ok": True, "commit_ok": co.returncode == 0}
        # fallback: shallow clone default branch
        subprocess.run(["git", "-C", dest, "fetch", "--depth", "50", "origin"],
                       capture_output=True)
        co = subprocess.run(["git", "-C", dest, "checkout", "-q", shortsha],
                            capture_output=True)
        return {"clone_ok": True, "commit_ok": co.returncode == 0,
                "note": "commit not directly fetchable; tried recent history"}
    except Exception as e:
        return {"clone_ok": False, "commit_ok": False, "error": str(e)}


def _head_matches(dest, shortsha):
    """Check the repo's current HEAD against the short SHA (prefix match)."""
    try:
        r = subprocess.run(["git", "-C", dest, "rev-parse", "HEAD"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            head = r.stdout.strip()
            return head.startswith(shortsha) or shortsha.startswith(head[:len(shortsha)])
    except Exception:
        pass
    return False


def resolve_by_clone(candidates, shortsha, dest, depth=50):
    """Token-free resolution: try `git clone` on each candidate owner/name split
    until one succeeds. Avoids the GitHub API rate limit entirely. Returns
    (owner, name, status_dict)."""
    # already on disk: verify the actual HEAD commit instead of assuming.
    if os.path.exists(dest) and os.path.exists(os.path.join(dest, ".git")):
        # recover owner/name from origin url if possible
        owner = name = None
        try:
            r = subprocess.run(["git", "-C", dest, "remote", "get-url", "origin"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                tail = r.stdout.strip().rstrip("/").replace(".git", "")
                bits = tail.split("/")
                if len(bits) >= 2:
                    owner, name = bits[-2], bits[-1]
        except Exception:
            pass
        return owner, name, {"clone_ok": True,
                             "commit_ok": _head_matches(dest, shortsha),
                             "note": "already present (HEAD re-verified)"}

    for owner, name in candidates:
        url = f"https://github.com/{owner}/{name}.git"
        if os.path.exists(dest):
            return owner, name, {"clone_ok": True, "commit_ok": None,
                                 "note": "already present"}
        try:
            os.makedirs(dest, exist_ok=True)
            subprocess.run(["git", "init", "-q", dest], check=True)
            subprocess.run(["git", "-C", dest, "remote", "add", "origin", url], check=True)
            fetched = subprocess.run(
                ["git", "-C", dest, "fetch", "--depth", "1", "origin", shortsha],
                capture_output=True)
            if fetched.returncode == 0:
                co = subprocess.run(["git", "-C", dest, "checkout", "-q", "FETCH_HEAD"],
                                    capture_output=True)
                return owner, name, {"clone_ok": True, "commit_ok": co.returncode == 0}
            # commit not directly fetchable -> shallow history then checkout
            f2 = subprocess.run(["git", "-C", dest, "fetch", "--depth", str(depth), "origin"],
                                capture_output=True)
            if f2.returncode == 0:
                co = subprocess.run(["git", "-C", dest, "checkout", "-q", shortsha],
                                    capture_output=True)
                return owner, name, {"clone_ok": True, "commit_ok": co.returncode == 0,
                                     "note": "commit via recent history" if co.returncode == 0
                                     else "cloned but commit not in shallow history"}
            # this split's remote doesn't exist -> clean up, try next candidate
            import shutil; shutil.rmtree(dest, ignore_errors=True)
        except Exception:
            import shutil; shutil.rmtree(dest, ignore_errors=True)
            continue
    return None, None, {"clone_ok": False, "commit_ok": False, "note": "no candidate resolved"}


def availability_report(repo_fields, clone_root, token=None, do_clone=True,
                        method="clone"):
    """Resolve (and optionally clone) each unique repo; return an availability
    report with rates and per-repo status.

    method='clone' (default): token-free, resolves by trying git clone on each
                              candidate split (no API rate limit).
    method='api':             uses the GitHub API (needs a token for >60 repos).
    """
    os.makedirs(clone_root, exist_ok=True)
    statuses = []
    counts = {"total": 0, "resolved": 0, "clone_ok": 0, "commit_ok": 0,
              "rate_limited": 0, "unresolved": 0}
    for rf in sorted(set(repo_fields)):
        counts["total"] += 1
        cands, sha = parse_repo_field(rf)
        st = {"repo_field": rf, "shortsha": sha}

        if method == "clone":
            dest = os.path.join(clone_root, rf)
            owner, name, res = resolve_by_clone(cands, sha, dest)
            st.update({"resolved": bool(owner), "owner": owner, "name": name})
            st.update(res); st["path"] = dest if owner else None
            if owner:
                counts["resolved"] += 1
                if res.get("clone_ok"): counts["clone_ok"] += 1
                if res.get("commit_ok"): counts["commit_ok"] += 1
            else:
                counts["unresolved"] += 1
            statuses.append(st); continue

        # --- api method (legacy; needs token at scale) ---
        owner, name, clone_url = resolve_on_github(cands, token=token)
        st.update({"resolved": bool(owner), "owner": owner, "name": name})
        if clone_url == "RATE_LIMITED":
            counts["rate_limited"] += 1; st["status"] = "RATE_LIMITED"
            statuses.append(st); continue
        if not owner:
            counts["unresolved"] += 1; st["status"] = "UNRESOLVED"
            statuses.append(st); continue
        counts["resolved"] += 1
        if do_clone:
            dest = os.path.join(clone_root, rf)
            res = clone_at_commit(clone_url, sha, dest)
            st.update(res); st["path"] = dest
            if res.get("clone_ok"): counts["clone_ok"] += 1
            if res.get("commit_ok"): counts["commit_ok"] += 1
        statuses.append(st)

    t = counts["total"] or 1
    return {
        "repos_total": counts["total"],
        "resolved": counts["resolved"],
        "resolved_rate": round(counts["resolved"] / t, 4),
        "clone_ok": counts["clone_ok"],
        "clone_success_rate": round(counts["clone_ok"] / t, 4),
        "commit_ok": counts["commit_ok"],
        "commit_availability_rate": round(counts["commit_ok"] / t, 4),
        "rate_limited": counts["rate_limited"],
        "unresolved": counts["unresolved"],
        "statuses": statuses,
    }
