#!/usr/bin/env python3
"""Download the unannotated traffic footage dataset from the NAS share."""

import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path, PurePosixPath


BASE_URL = "https://nas.fastiuk.com"
SHARE_ID = "dzkwUEM3I"
SHARE_URL = f"{BASE_URL}/sharing/{SHARE_ID}"
TARGET_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "video-footage-dataset"


def curl(args, *, text=True):
    result = subprocess.run(["curl", *args], check=True, stdout=subprocess.PIPE)
    return result.stdout.decode("utf-8") if text else result.stdout


def api(params, cookie_file):
    url = f"{BASE_URL}/webapi/entry.cgi?{urllib.parse.urlencode(params)}"
    return curl(["-sS", "-L", "-b", cookie_file, "-c", cookie_file, url])


def local_name(remote_name):
    path = PurePosixPath(remote_name)
    stem = re.sub(r"^vecteezy[_-]+", "", path.stem, flags=re.I)
    stem = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_").lower()
    stem = re.sub(r"_+", "_", stem)
    return stem + path.suffix.lower()


def download_url(remote_path, filename):
    params = {
        "api": "SYNO.FolderSharing.Download",
        "version": "2",
        "method": "download",
        "mode": "download",
        "stdhtml": "true",
        "_sharing_id": SHARE_ID,
        "dlname": filename,
        "path": json.dumps([remote_path], separators=(",", ":")),
    }
    return f"{BASE_URL}/webapi/entry.cgi?{urllib.parse.urlencode(params)}"


def remote_folder(cookie_file):
    session_js = api(
        {
            "api": "SYNO.Core.Sharing.Session",
            "version": "1",
            "method": "get",
            "sharing_id": json.dumps(SHARE_ID),
            "sharing_status": json.dumps("none"),
        },
        cookie_file,
    )
    match = re.search(r"SYNO\.SDS\.ExtraSession\s*=\s*(\{.*?\})\s*;", session_js, re.S)
    if not match:
        raise RuntimeError("Cannot find shared folder name in Synology response")
    data = json.loads(match.group(1))
    return "/" + data["filename"]


def remote_files(folder, cookie_file):
    manifest = json.loads(
        api(
            {
                "api": "SYNO.FolderSharing.List",
                "version": "2",
                "method": "list",
                "_sharing_id": SHARE_ID,
                "user": "",
                "folder_path": json.dumps(folder),
                "offset": "0",
                "limit": "1000",
                "additional": json.dumps(["size"]),
            },
            cookie_file,
        )
    )
    if not manifest.get("success"):
        raise RuntimeError(f"Cannot list remote files: {manifest}")
    return [item for item in manifest["data"]["files"] if not item.get("isdir")]


def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile() as cookie:
        cookie_file = cookie.name

        print(f"Opening share: {SHARE_URL}")
        curl(["-sS", "-L", "-b", cookie_file, "-c", cookie_file, SHARE_URL])

        print("Creating sharing session...")
        api(
            {
                "api": "SYNO.Core.Sharing.Login",
                "version": "1",
                "method": "login",
                "sharing_id": SHARE_ID,
            },
            cookie_file,
        )

        folder = remote_folder(cookie_file)
        print(f"Reading remote manifest: {folder}")

        for item in sorted(remote_files(folder, cookie_file), key=lambda value: value["name"]):
            filename = local_name(item["name"])
            expected_size = int(item["additional"]["size"])
            target = TARGET_DIR / filename
            part = TARGET_DIR / f"{filename}.part"

            if target.exists() and target.stat().st_size == expected_size:
                print(f"Already present: {filename} ({expected_size} bytes)")
                continue

            if target.exists():
                print(f"Replacing incomplete file: {filename}")
                target.unlink()

            print(f"Downloading {filename}...")
            curl(
                [
                    "-L",
                    "--fail",
                    "--continue-at",
                    "-",
                    "--retry",
                    "3",
                    "--retry-delay",
                    "5",
                    "-b",
                    cookie_file,
                    "-o",
                    str(part),
                    download_url(item["path"], filename),
                ],
                text=False,
            )

            actual_size = part.stat().st_size
            if actual_size != expected_size:
                raise RuntimeError(
                    f"Size mismatch for {filename}: got {actual_size}, expected {expected_size}"
                )
            part.replace(target)

    print(f"Video footage dataset ready under: {TARGET_DIR}")


if __name__ == "__main__":
    main()
