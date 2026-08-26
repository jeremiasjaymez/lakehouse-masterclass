import requests

BASE = "http://localhost:19120/api/v1"


def get_hash(branch="main"):
    r = requests.get(f"{BASE}/trees/tree/{branch}")
    r.raise_for_status()
    return r.json()["hash"]


def create_branch(name, source="main"):
    source_hash = get_hash(source)
    r = requests.post(
        f"{BASE}/trees/tree",
        params={"sourceRefName": source},
        json={"type": "BRANCH", "name": name, "hash": source_hash},
    )
    if r.status_code == 200:
        print(f"Created branch '{name}' from '{source}' @ {source_hash[:12]}...")
    else:
        print(f"Failed to create '{name}': {r.status_code} {r.text}")


create_branch("dev")
create_branch("staging")
create_branch("prod")

# Verify
refs = requests.get(f"{BASE}/trees").json()["references"]
print("\nAll branches:")
for ref in refs:
    print(f"  {ref['name']}")
