# version_utils.py
import re, sys

VERSION_FILE = "config.py"  # хранить версию здесь

def read_version():
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        s = f.read()
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', s)
    return m.group(1) if m else "0.0.0"

def write_version(new):
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        s = f.read()
    ns = re.sub(r'(__version__\s*=\s*["\'])([^"\']+)(["\'])',
                r'\1' + new + r'\3', s)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(ns)

def bump(part):
    v = read_version().split(".")
    major, minor, patch = map(int, v)
    if part == "major":
        major += 1; minor = 0; patch = 0
    elif part == "minor":
        minor += 1; patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError("Unknown part")
    new = f"{major}.{minor}.{patch}"
    write_version(new)
    print(new)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python version_utils.py bump <major|minor|patch>")
    else:
        bump(sys.argv[2])
