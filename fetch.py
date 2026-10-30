#!/usr/bin/env python3
import configparser
import subprocess
import sys
import os
import shutil

REPO_DIR = "linphone-sdk"
SOURCE_URL = "https://github.com/BelledonneCommunications/linphone-sdk.git"

MIRRORS = {
    "external/mbedtls": "https://github.com/Mbed-TLS/mbedtls.git",
    "external/speex": "https://github.com/xiph/speex.git",
    "external/libvpx": "https://github.com/webmproject/libvpx.git",
    "external/opus": "https://github.com/xiph/opus.git",
    "external/srtp": "https://github.com/cisco/libsrtp.git",
    "external/libxml2": "https://github.com/GNOME/libxml2.git",
    "external/zlib": "https://github.com/madler/zlib.git",
    "external/openh264": "https://github.com/cisco/openh264.git",
    "external/libjpeg-turbo": "https://github.com/libjpeg-turbo/libjpeg-turbo.git",
    "external/xerces-c": "https://github.com/apache/xerces-c.git",
    "external/soci": "https://github.com/SOCI/soci.git",
    "external/sqlite3": "https://github.com/sqlite/sqlite.git",
    "external/codec2": "https://github.com/drowe67/codec2.git",
    "external/zxing-cpp": "https://github.com/zxing-cpp/zxing-cpp.git",
    "external/vo-amrwbenc": "https://github.com/mstorsjo/vo-amrwbenc.git",
    "external/openldap": "https://github.com/openldap/openldap.git",
    "external/jsoncpp": "https://github.com/open-source-parsers/jsoncpp.git",
    "external/liboqs": "https://github.com/open-quantum-safe/liboqs.git",
    "external/rnnoise": "https://github.com/xiph/rnnoise.git",
    "belle-sip/tester/cpp-httplib": "https://github.com/yhirose/cpp-httplib.git",
    "external/dav1d": "https://github.com/videolan/dav1d.git",
}

def run(cmd, cwd=None, timeout=300):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"

def main():
    log = open("report.txt", "w")

    def w(s):
        print(s)
        log.write(s + "\n")

    if os.path.isdir(REPO_DIR):
        shutil.rmtree(REPO_DIR)

    w(f"=== Cloning top-level linphone-sdk from {SOURCE_URL} ===")
    rc, out = run(["git", "clone", "--depth", "1", SOURCE_URL, REPO_DIR], timeout=600)
    w(out)
    if rc != 0:
        w("FATAL: could not even clone the top-level linphone-sdk from GitHub mirror.")
        log.close()
        sys.exit(1)

    gitmodules = os.path.join(REPO_DIR, ".gitmodules")
    cp = configparser.ConfigParser()
    cp.read(gitmodules)

    submods = []
    for section in cp.sections():
        name = section.split('"')[1] if '"' in section else section
        path = cp[section]["path"]
        url = cp[section]["url"].strip()
        submods.append((name, path, url))

    w(f"\nFound {len(submods)} submodules.\n")

    ok_list = []
    fail_list = []

    for name, path, url in submods:
        w(f"=== {path}  (declared url: {url}) ===")
        if "gitlab.linphone.org" in url:
            mirror = MIRRORS.get(path)
            if mirror:
                w(f"  -> overriding with mirror: {mirror}")
                run(["git", "config", f"submodule.{name}.url", mirror], cwd=REPO_DIR)
            else:
                w("  -> no known mirror for this one, leaving as-is (will likely fail)")

        rc, out = run(
            ["git", "submodule", "update", "--init", "--depth", "1", "--", path],
            cwd=REPO_DIR,
            timeout=300,
        )
        w(out)
        if rc == 0:
            w("  RESULT: OK\n")
            ok_list.append(path)
        else:
            w("  RESULT: FAILED\n")
            fail_list.append(path)

    w("\n\n================ SUMMARY ================")
    w(f"OK ({len(ok_list)}): " + ", ".join(ok_list))
    w(f"FAILED ({len(fail_list)}): " + ", ".join(fail_list))
    log.close()

if __name__ == "__main__":
    main()
