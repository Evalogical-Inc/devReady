"""Print the Homebrew formula for a devready-cli release on PyPI.

Usage: python scripts/render_homebrew_formula.py [VERSION]   (default: latest)

Release tooling only; not shipped in the package. The sdist URL and sha256 come from
PyPI's JSON API, so the formula always matches what was published.
"""

import json
import sys
import urllib.request

FORMULA = """class Devready < Formula
  include Language::Python::Virtualenv

  desc "Local-first, read-only CLI that checks a project's environment requirements"
  homepage "https://devready-ten.vercel.app/"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/devready --version")
    assert_match "git", shell_output("#{{bin}}/devready explain git.version")
  end
end
"""


def render(release: dict) -> str:
    """release: the PyPI JSON for one version (a dict with a "urls" list)."""
    sdists = [u for u in release["urls"] if u["packagetype"] == "sdist"]
    if len(sdists) != 1:
        raise ValueError("expected exactly one sdist on PyPI")
    return FORMULA.format(url=sdists[0]["url"], sha256=sdists[0]["digests"]["sha256"])


def main(argv: list[str]) -> int:
    path = f"{argv[1]}/" if len(argv) > 1 else ""
    url = f"https://pypi.org/pypi/devready-cli/{path}json"
    with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 (fixed https URL)
        sys.stdout.write(render(json.load(resp)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
