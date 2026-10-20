# Created by 青云 on 2026/10/20.
"""Pages Dashboard 健康检查：自动发现开启了 GitHub Pages 的仓库，检查定时任务、最近运行、60 天停用倒计时、页面可访问性。

在 GitHub Actions 里用 GITHUB_TOKEN 调 API（1000 次/小时）；本地没有 token 时只有 60 次/小时，一次完整检查约 25 次请求。
只用标准库。
"""
import json, os, re, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "health.json"
OWNER = "climb0516"
CST = timezone(timedelta(hours=8))
INACTIVE_DAYS = 60          # 公开仓库 60 天无活动，定时任务会被 GitHub 停用
UA = "pages-dashboard-health"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "User-Agent": UA, "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def raw(repo, branch, path):
    url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/{branch}/{path}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=15) as r:
        return r.read().decode("utf-8", "ignore")


def page_status(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def cron_interval_hours(cron):
    """粗略估计 cron 的执行间隔（小时），用于判断「该跑没跑」。"""
    parts = cron.split()
    if len(parts) != 5:
        return None
    minute, hour, dom, _, dow = parts
    if hour == "*":
        return 1
    m = re.fullmatch(r"\*/(\d+)", hour)
    if m:
        return int(m.group(1))
    if "," in hour:
        return 24 / len(hour.split(","))
    if dow not in ("*", "?") or dom not in ("*", "?"):
        return 24 * 7
    return 24


def check_repo(r):
    name, branch = r["name"], r["default_branch"]
    page = (f"https://{OWNER.lower()}.github.io/" if name.lower() == f"{OWNER.lower()}.github.io"
            else f"https://{OWNER.lower()}.github.io/{name}/")
    pushed = parse_time(r["pushed_at"])
    now = datetime.now(timezone.utc)
    idle_days = (now - pushed).total_seconds() / 86400
    item = {
        "name": name, "page": page, "repo_url": r["html_url"], "description": r.get("description") or "",
        "pushed_at": r["pushed_at"], "idle_days": round(idle_days, 1),
        "days_left": round(INACTIVE_DAYS - idle_days, 1),
        "page_status": page_status(page), "workflows": [], "issues": [],
    }

    wfs = [w for w in api(f"/repos/{OWNER}/{name}/actions/workflows")["workflows"]
           if not w["path"].startswith("dynamic/")]          # 排除 GitHub 自动的 pages-build-deployment
    for w in wfs:
        wf = {"name": w["name"], "path": w["path"], "state": w["state"], "url": w["html_url"],
              "cron": None, "interval_h": None, "last_run": None, "last_success_at": None, "last_scheduled_at": None}
        try:
            m = re.search(r"cron:\s*['\"]([^'\"]+)['\"]", raw(name, branch, w["path"]))
            if m:
                wf["cron"] = m.group(1)
                wf["interval_h"] = cron_interval_hours(m.group(1))
        except Exception:
            pass
        runs = api(f"/repos/{OWNER}/{name}/actions/workflows/{w['id']}/runs?per_page=15")["workflow_runs"]
        if runs:
            x = runs[0]
            wf["last_run"] = {"status": x["status"], "conclusion": x["conclusion"], "event": x["event"],
                              "created_at": x["created_at"], "url": x["html_url"]}
            wf["last_success_at"] = next((y["created_at"] for y in runs if y["conclusion"] == "success"), None)
            wf["last_scheduled_at"] = next((y["created_at"] for y in runs if y["event"] == "schedule"), None)
        item["workflows"].append(wf)

    # ── 判定问题 ──
    issues = item["issues"]
    if item["page_status"] != 200:
        issues.append(("error", f"页面返回 {item['page_status'] or '无法访问'}"))
    for wf in item["workflows"]:
        if wf["state"] != "active":
            reason = "60 天无活动被 GitHub 停用" if wf["state"] == "disabled_inactivity" else f"已停用（{wf['state']}）"
            issues.append(("error", f"{wf['name']}：{reason}"))
            continue
        lr = wf["last_run"]
        if lr and lr["status"] == "completed" and lr["conclusion"] not in ("success", "skipped"):
            issues.append(("error", f"{wf['name']}：最近一次运行失败（{lr['conclusion']}）"))
        if wf["interval_h"] and lr:
            # 以最近一次任何运行（定时 / 手动 / push）为基准：刚上线或刚修好的站还没轮到定时，不算异常
            last = max(t for t in (parse_time(wf["last_scheduled_at"]), parse_time(lr["created_at"])) if t)
            # GitHub 定时任务常延迟，允许 2 倍间隔 + 1 小时
            limit = timedelta(hours=wf["interval_h"] * 2 + 1)
            if now - last > limit:
                issues.append(("warn", f"{wf['name']}：超过 {wf['interval_h'] * 2 + 1:g} 小时没有运行"))
    if item["workflows"] and any(w["cron"] for w in item["workflows"]):
        if item["days_left"] < 14:
            issues.append(("warn" if item["days_left"] > 0 else "error",
                           f"仓库 {idle_days:.0f} 天无提交，定时任务 {max(0, item['days_left']):.0f} 天后会被停用"))
    item["level"] = "error" if any(l == "error" for l, _ in issues) else "warn" if issues else "ok"
    item["issues"] = [{"level": l, "text": t} for l, t in issues]
    return item


def main():
    repos = api(f"/users/{OWNER}/repos?per_page=100&type=owner")
    pages = [r for r in repos if r["has_pages"] and not r["archived"]]
    # 自己（pages-dashboard）还没开启 Pages 时也要检查
    if not any(r["name"] == "pages-dashboard" for r in pages):
        pages += [r for r in repos if r["name"] == "pages-dashboard"]
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda r: _safe(check_repo, r), pages))
    results.sort(key=lambda x: ({"error": 0, "warn": 1, "ok": 2}.get(x["level"], 3), x["pushed_at"] and -parse_time(x["pushed_at"]).timestamp()))
    data = {
        "updated": datetime.now(CST).isoformat(timespec="seconds"),   # 每次都变 = 心跳
        "owner": OWNER,
        "authenticated": bool(TOKEN),
        "repos": results,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    for x in results:
        print(f"{x['level']:5} {x['name']:20} wf={len(x['workflows'])} page={x['page_status']} left={x['days_left']}d", [i["text"] for i in x["issues"]])


def _safe(fn, r):
    try:
        return fn(r)
    except Exception as e:
        return {"name": r["name"], "page": f"https://{OWNER.lower()}.github.io/{r['name']}/", "repo_url": r["html_url"],
                "description": r.get("description") or "", "pushed_at": r["pushed_at"], "idle_days": None, "days_left": None,
                "page_status": None, "workflows": [], "level": "warn",
                "issues": [{"level": "warn", "text": f"健康检查失败：{str(e)[:100]}"}]}


if __name__ == "__main__":
    main()
