import requests
from dataclasses import dataclass
from typing import List, Tuple
from jinja2 import Template
import os


GITHUB_USER = os.environ.get("GITHUB_USER", "")
PERSONAL_ACCESS_TOKEN = os.environ.get("PERSONAL_ACCESS_TOKEN", "")


@dataclass
class Fork:
    parent_user: str
    parent_name: str
    owner: str
    name: str
    branches: List[Tuple[str, str]]
    parent_branches: List[str]
    parent_default_branch: str


def run_graphql_query(query):
    headers = {"Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}"}
    request = requests.post(
        "https://api.github.com/graphql", json={"query": query}, headers=headers
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Query failed to run by returning code {request.status_code}")


def run_rest_query(url):
    headers = {"Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}"}
    request = requests.get(url=url, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            f"Query failed to run for url {url} by returning code {request.status_code}"
        )


def get_forks(user):
    query = Template(
        """
{
  user(login: "{{ user }}") {
    name
    url
    repositories(first: 100, isFork: true) {
      edges {
        node {
          name
          parent {
            nameWithOwner
          }
          owner {
            login
          }
          refs(first: 100, refPrefix: "refs/heads/") {
            edges {
              node {
                name
                target {
                  oid
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
    )
    result = run_graphql_query(query.render(user=user))
    forks = []
    for fork in result["data"]["user"]["repositories"]["edges"]:
        name = fork["node"]["name"]
        parent = fork["node"]["parent"]["nameWithOwner"]
        parent_user, parent_name = tuple(parent.split("/"))
        owner = fork["node"]["owner"]["login"]
        branches = [
            (x["node"]["name"], x["node"]["target"]["oid"])
            for x in fork["node"]["refs"]["edges"]
        ]
        forks.append(
            Fork(
                parent_user=parent_user,
                parent_name=parent_name,
                owner=owner,
                name=name,
                branches=branches,
                parent_branches=None,
                parent_default_branch=None,
            )
        )
    return forks


def get_branches(forks):
    s = []
    s.append("{")
    for i, fork in enumerate(forks):
        s.append(
            f'  parent_{i}: repository(owner: "{fork.parent_user}", name: "{fork.parent_name}") {{'
        )
        s.append('    refs(first: 100, refPrefix: "refs/heads/") {')
        s.append("      edges {")
        s.append("        node {")
        s.append("          name")
        s.append("        }")
        s.append("      }")
        s.append("    }")
        s.append("    defaultBranchRef {")
        s.append("      name")
        s.append("    }")
        s.append("  }")
    s.append("}")

    query = "\n".join(s)

    result = run_graphql_query(query)

    for parent, fork in zip(result["data"].keys(), forks):
        fork.parent_default_branch = result["data"][parent]["defaultBranchRef"]["name"]
        fork.parent_branches = []
        for branch in result["data"][parent]["refs"]["edges"]:
            fork.parent_branches.append(branch["node"]["name"])

    return forks


def branch_contains_sha(user, repo, branch, sha):
    url = f"https://api.github.com/repos/{user}/{repo}/compare/{branch}...{sha}"
    result = run_rest_query(url)
    ahead_by = int(result["ahead_by"])
    return ahead_by < 1


def fork_is_merged(fork):
    for (branch, sha) in fork.branches:
        if branch in fork.parent_branches:
            if not branch_contains_sha(fork.parent_user, fork.parent_name, branch, sha):
                return False
        else:
            # if the branch does not exist on parent, then we check whether the default branch contains the sha
            default_branch = fork.parent_default_branch
            if not branch_contains_sha(
                fork.parent_user, fork.parent_name, default_branch, sha
            ):
                return False
    return True


forks = get_forks(GITHUB_USER)
forks = get_branches(forks)
leftover_forks = []
for fork in forks:
    if fork_is_merged(fork):
        leftover_forks.append(f"https://github.com/{fork.owner}/{fork.name}")

print("Forks which are either merged or not modified:")
if len(leftover_forks) == 0:
    print(f"- no such forks found")
else:
    for fork in leftover_forks:
        print(f"- {fork}")
