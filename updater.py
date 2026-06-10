import requests
import json
import os
import subprocess
import sys
import shutil

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/hunterh-sudo/Remote-BPM/main/version.json"

LOCAL_VERSION_FILE = "version.json"


def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return "0.0.0"

    with open(LOCAL_VERSION_FILE, "r") as f:
        return json.load(f).get("version", "0.0.0")


def get_remote_version():
    try:
        r = requests.get(GITHUB_VERSION_URL, timeout=5)
        return r.json()["version"]
    except:
        return None


def update_needed(local, remote):
    if remote is None:
        return False
    return remote != local


def download_latest_repo():
    """
    Simple approach: pull zip of repo
    """
    zip_url = "https://codeload.github.com/HunterH-Sudo/Remote-BPM/zip/refs/heads/main"

    r = requests.get(zip_url, stream=True)
    with open("update.zip", "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    # extract
    shutil.unpack_archive("update.zip", "update_tmp")

    # find extracted folder
    extracted = os.listdir("update_tmp")[0]
    src = os.path.join("update_tmp", extracted)

    # copy over files (overwrite current project)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(".", item)

        if os.path.isdir(s):
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


def run_update_if_needed():
    local = get_local_version()
    remote = get_remote_version()

    print(f"Local: {local} | Remote: {remote}")

    if update_needed(local, remote):
        print("Update found. Updating...")

        download_latest_repo()

        print("Update complete. Restart required.")
        os.execv(sys.executable, ["python"] + sys.argv)

    else:
        print("No update needed.")