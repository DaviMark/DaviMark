"""Baixa o histórico de contribuições do GitHub (GraphQL) para data/contributions.json.

Variáveis de ambiente:
  GH_LOGIN  usuário do GitHub (padrão: DaviMark)
  GH_TOKEN  token (no Actions: secrets.GH_PAT ou o GITHUB_TOKEN padrão)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

import urllib.request

from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

API = "https://api.github.com/graphql"

Q_USER = """query($login:String!){ user(login:$login){
  createdAt
  followers { totalCount }
  repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) { totalCount nodes { stargazerCount } }
} }"""
Q_YEAR = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      contributionCalendar{ weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""


def gql(token: str, query: str, variables: dict) -> dict:
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def main() -> None:
    login = os.environ.get("GH_LOGIN", "DaviMark")
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN não definido")

    user = gql(token, Q_USER, {"login": login})["user"]
    created = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    stats = {
        "repositorios": user["repositories"]["totalCount"],
        "estrelas": sum(n["stargazerCount"] for n in user["repositories"]["nodes"]),
        "seguidores": user["followers"]["totalCount"],
    }
    (DATA_FILE.parent / "github_stats.json").parent.mkdir(parents=True, exist_ok=True)
    (DATA_FILE.parent / "github_stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    now = dt.datetime.now(dt.timezone.utc)

    days: dict[str, int] = {}
    start = created
    while start < now:  # a API aceita no máximo 1 ano por consulta
        end = min(start + dt.timedelta(days=365), now)
        data = gql(token, Q_YEAR, {"login": login, "from": start.isoformat(), "to": end.isoformat()})
        for week in data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
        start = end

    out = {
        "login": login,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": [{"date": k, "count": v} for k, v in sorted(days.items())],
    }
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(out, indent=0), encoding="utf-8")
    print(f"{len(days)} dias salvos, {sum(days.values())} contribuições no total")


if __name__ == "__main__":
    main()
