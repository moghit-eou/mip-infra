#!/usr/bin/env python3
"""Demo: render a few components by hand, one adapter each, then scan _rendered/.

    python3 render_demo.py
    checkov -d _rendered --framework kubernetes
"""
import os
import subprocess

OUT = "_rendered"


def run(cmd):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def save(owner, name, text):
    os.makedirs(f"{OUT}/{owner}", exist_ok=True)
    with open(f"{OUT}/{owner}/{name}.yaml", "w") as f:
        f.write(text)


# ---------- the 3 adapters ----------

def kustomize(folder):
    return run(["kustomize", "build", folder])


def helm(name, folder, namespace, value_files):
    cmd = ["helm", "template", name, folder, "--namespace", namespace]
    for f in value_files:
        cmd += ["--values", f]
    return run(cmd)


def plain(folder):
    return run(["bash", "-c", f"cat {folder}/*.yaml"])


def download(repo, commit, folder):
    """Get another repo at a pinned commit (level 3)."""
    run(["git", "init", "-q", folder])
    run(["git", "-C", folder, "fetch", "-q", "--depth", "1", repo, commit])
    run(["git", "-C", folder, "checkout", "-q", "FETCH_HEAD"])


# ---------- the scanned components, written by hand ----------

# kustomize, in mip-infra
save("ours", "athena-proxy", kustomize("common/athena-proxy/manifests"))

# plain YAML, applied by hand
save("ours", "rbac", plain("base/mip-infrastructure/rbac"))

# Helm, chart in mip-infra (ECK: values are inline in eck-stack.yaml, copied to a file first)
run(["bash", "-c", "yq '.spec.source.helm.values' common/monitoring/eck-stack.yaml > /tmp/eck-values.yaml"])
save("ours", "eck-stack", helm("eck", "common/monitoring/eck", "elastic-system", ["/tmp/eck-values.yaml"]))

# Helm, chart from another repo (the 3-level example)
download("https://github.com/madgik/exaflow", "e8c15aaf37cc8ade5e2fa4de0bb769f7e2da4dac", "/tmp/exaflow")
save("upstream", "federation-a-exareme2", helm(
    "federation-a-exareme2", "/tmp/exaflow/kubernetes", "federation-a", [
        "/tmp/exaflow/kubernetes/values.yaml",
        "deployments/shared-apps/exareme2/values.yaml",
        "deployments/local/federations/federation-A/customizations/exareme2-values.yaml",
    ]))

print(f"\ndone, see {OUT}/ours and {OUT}/upstream")