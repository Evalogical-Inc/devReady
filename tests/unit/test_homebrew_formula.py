import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "render_homebrew_formula.py"
spec = importlib.util.spec_from_file_location("render_homebrew_formula", SCRIPT)
render_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_mod)

URL = "https://files.pythonhosted.org/packages/aa/bb/cc/devready_cli-9.9.9.tar.gz"
SHA = "a" * 64


def release(*sdists):
    return {
        "urls": [{"packagetype": "bdist_wheel", "url": "x", "digests": {"sha256": "x"}}]
        + [{"packagetype": "sdist", "url": u, "digests": {"sha256": s}} for u, s in sdists]
    }


def test_formula_uses_the_sdist_url_and_sha():
    out = render_mod.render(release((URL, SHA)))
    assert f'url "{URL}"' in out
    assert f'sha256 "{SHA}"' in out
    assert 'assert_match version.to_s, shell_output("#{bin}/devready --version")' in out


@pytest.mark.parametrize("sdists", [[], [(URL, SHA), (URL, SHA)]])
def test_needs_exactly_one_sdist(sdists):
    with pytest.raises(ValueError):
        render_mod.render(release(*sdists))
