#!/usr/bin/env python

import pathlib
import subprocess
from typing import List


def findDotRepos() -> List[pathlib.Path]:

    return pathlib.Path(".").glob("**/*.repos")


def main():

    cloned_repos = []

    while True:

        found_repos = findDotRepos()
        remaining_repos = set(found_repos) - set(cloned_repos)

        if not remaining_repos:
            break

        next_repo = list(remaining_repos)[0]
        with open(str(next_repo), "r") as f:
            proc = subprocess.run(["vcs", "import", "./upstream/", "--recursive"], stdin=f)
            if proc.returncode != 0:
                raise RuntimeError("vcs import failed")
        
        cloned_repos.append(next_repo)


if __name__ == "__main__":
    main()
