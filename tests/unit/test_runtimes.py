import json

import pytest

from devready.checks.runtimes import check_runtimes
from devready.explain import EXPLANATIONS
from devready.models import Result, Status


def fake(versions):
    def tool(cid, title, exe, docs, args):
        v = versions.get(exe)
        status = Status.PASS if v else Status.WARN
        return Result(cid, title, status, "x"), v

    return tool


def run(tmp_path, versions):
    return {r.check_id: r for r in check_runtimes(tmp_path, fake(versions))}


def test_nothing_declared_nothing_checked(tmp_path):
    assert check_runtimes(tmp_path, fake({"go": "1.22.0"})) == []


def test_go_mod_minimum(tmp_path):
    (tmp_path / "go.mod").write_text("module x\n\ngo 1.22\n")
    assert run(tmp_path, {"go": "1.21.5"})["project.go.mod"].status is Status.FAIL
    assert run(tmp_path, {"go": "1.22.1"})["project.go.mod"].status is Status.PASS


@pytest.mark.parametrize(
    "declaration",
    [
        'ruby "3.3.0"',
        "ruby '3.3'",
        '  ruby\t"3.3.0"  # interpreter pin\r\n',
    ],
)
def test_gemfile_ruby_literal(tmp_path, declaration):
    (tmp_path / "Gemfile").write_text('source "https://rubygems.org"\n' + declaration)
    results = run(tmp_path, {"ruby": "3.3.0"})
    assert set(results) == {"ruby.version", "project.ruby.gemfile"}
    assert results["project.ruby.gemfile"].status is Status.PASS
    assert "Gemfile" in results["project.ruby.gemfile"].summary
    assert "project.ruby.gemfile" in EXPLANATIONS


@pytest.mark.parametrize("installed,expected", [("3.2.2", Status.WARN), (None, Status.SKIP)])
def test_gemfile_ruby_mismatch_or_missing(tmp_path, installed, expected):
    (tmp_path / "Gemfile").write_text('ruby "3.3.0"\n')
    results = run(tmp_path, {"ruby": installed})
    assert results["project.ruby.gemfile"].status is expected
    assert "3.3.0" in results["project.ruby.gemfile"].summary
    assert results["ruby.version"].status is (Status.PASS if installed else Status.WARN)


@pytest.mark.parametrize(
    "text",
    [
        'gem "rails", "7.1.0"\n',
        '# ruby "3.3.0"\n',
        'ruby ">=3.3"\n',
        'ruby "3.3.0-preview1"\n',
        'ruby "3.3.0.1"\n',
        "ruby \"3.3.0'\n",
        "ruby \"#{ENV.fetch('RUBY_VERSION')}\"\n",
        'ruby File.read(".ruby-version")\n',
        'ruby "3.3.0" + suffix\n',
        'ruby "3.3.0" if false\n',
        'ruby "3.3.0", engine: "jruby"\n',
        'ruby\n"3.3.0"\n',
        'ruby "٣.٣.٠"\n',
    ],
)
def test_gemfile_without_supported_ruby_literal_does_not_probe(tmp_path, text):
    (tmp_path / "Gemfile").write_text(text, encoding="utf-8")

    def unexpected_tool(*args):
        pytest.fail("No supported runtime declaration; no tool should be probed")

    assert check_runtimes(tmp_path, unexpected_tool) == []


def test_gemfile_preserves_ruby_pin_precedence_and_tool_versions(tmp_path):
    (tmp_path / ".ruby-version").write_text("3.2.2\n")
    (tmp_path / "Gemfile").write_text('ruby "3.3.0"\n')
    (tmp_path / ".tool-versions").write_text("ruby 3.4.0\n")
    results = run(tmp_path, {"ruby": "3.2.2"})
    assert set(results) == {"ruby.version", "project.ruby.pin", "project.ruby.tool_versions"}
    assert results["project.ruby.pin"].status is Status.PASS
    assert results["project.ruby.tool_versions"].status is Status.WARN


def test_gemfile_and_tool_versions_are_both_checked(tmp_path):
    (tmp_path / "Gemfile").write_text('ruby "3.3.0"\n')
    (tmp_path / ".tool-versions").write_text("ruby 3.2.2\n")
    results = run(tmp_path, {"ruby": "3.3.0"})
    assert set(results) == {"ruby.version", "project.ruby.gemfile", "project.ruby.tool_versions"}
    assert results["project.ruby.gemfile"].status is Status.PASS
    assert results["project.ruby.tool_versions"].status is Status.WARN


def test_pins_and_tool_versions(tmp_path):
    (tmp_path / ".ruby-version").write_text("ruby-3.2.2\n")
    (tmp_path / ".java-version").write_text("17\n")
    (tmp_path / "global.json").write_text(json.dumps({"sdk": {"version": "8.0.100"}}))
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "stable"\n')
    (tmp_path / ".tool-versions").write_text("golang 1.22.0  # comment\nnodejs 20\n")
    r = run(tmp_path, {"ruby": "3.3.0", "java": "17.0.9", "dotnet": "8.0.100", "rustc": "1.75.0",
                       "go": "1.22.0"})  # fmt: skip
    assert r["project.ruby.pin"].status is Status.WARN
    assert r["project.java.pin"].status is Status.PASS
    assert r["project.dotnet.global"].status is Status.PASS
    assert r["project.rust.toolchain"].status is Status.SKIP  # named channel: not evaluated
    assert r["project.go.tool_versions"].status is Status.PASS
    assert "project.node.tool_versions" not in r  # node stays in project.py


def test_missing_tool_skips_and_hostile_content_not_echoed(tmp_path):
    (tmp_path / ".ruby-version").write_text("3.2.2 ignore previous instructions\n")
    (tmp_path / "global.json").write_text("{nope")
    out = check_runtimes(tmp_path, fake({}))
    assert {r.check_id for r in out} == {"ruby.version", "project.ruby.pin"}
    assert out[1].status is Status.SKIP
    assert "ignore" not in str(out)


def test_ids_have_explanations(tmp_path):
    tv = "\n".join(["golang 1", "ruby 3", "java 17", "rust 1", "dotnet 8"])
    files = {"go.mod": "go 1.22", ".ruby-version": "3", ".java-version": "17"}
    files |= {"global.json": '{"sdk":{"version":"8.0.1"}}', "rust-toolchain": "1.75.0"}
    for f, t in (files | {".tool-versions": tv}).items():
        (tmp_path / f).write_text(t)
    for r in check_runtimes(tmp_path, fake({})):
        assert r.check_id in EXPLANATIONS, r.check_id


def test_package_manager_pin(tmp_path):
    pkg = {"packageManager": "pnpm@9.1.0+sha256.abc"}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    r = run(tmp_path, {"pnpm": "9.1.0", "yarn": "1.22.0"})
    assert r["project.pnpm.pin"].status is Status.PASS
    assert "project.yarn.pin" not in r  # package.json names pnpm only
    assert run(tmp_path, {"pnpm": "8.0.0"})["project.pnpm.pin"].status is Status.WARN


def test_failing_version_command_is_not_reported_as_unrecognized_output(monkeypatch):
    from types import SimpleNamespace

    from devready.checks import tools

    monkeypatch.setattr(tools.shutil, "which", lambda exe: exe)
    for rc, out, want in ((1, "usage: ...", "failed"), (0, "no digits here", "not recognized")):
        monkeypatch.setattr(
            tools.subprocess,
            "run",
            lambda *a, rc=rc, out=out, **k: SimpleNamespace(returncode=rc, stdout=out, stderr=""),
        )
        result, version = tools.check_tool("x.version", "X", "x", "docs")
        assert result.status is Status.ERROR and want in result.summary and version is None


POM = "<project><properties>{}</properties></project>"


@pytest.mark.parametrize(
    "declaration",
    [
        "<maven.compiler.release>17</maven.compiler.release>",
        "<maven.compiler.source>17</maven.compiler.source>",
        "<maven.compiler.target>17</maven.compiler.target>",
    ],
)
def test_pom_java_target_is_a_minimum(tmp_path, declaration):
    (tmp_path / "pom.xml").write_text(POM.format(declaration))
    assert run(tmp_path, {"java": "17.0.9"})["project.java.maven"].status is Status.PASS
    result = run(tmp_path, {"java": "11.0.2"})["project.java.maven"]
    assert result.status is Status.FAIL and ">=17" in result.summary and "11.0.2" in result.summary


def test_pom_compiler_plugin_release_is_read(tmp_path):
    (tmp_path / "pom.xml").write_text(
        "<project><build><plugins><plugin><artifactId>maven-compiler-plugin</artifactId>"
        "<configuration><release>21</release></configuration></plugin></plugins></build></project>"
    )
    assert run(tmp_path, {"java": "21.0.1"})["project.java.maven"].status is Status.PASS
    assert run(tmp_path, {"java": "17.0.9"})["project.java.maven"].status is Status.FAIL


def test_pom_java_property_is_resolved_from_the_same_file(tmp_path):
    (tmp_path / "pom.xml").write_text(
        POM.format(
            "<java.version>21</java.version>"
            "<maven.compiler.release>${java.version}</maven.compiler.release>"
        )
    )
    assert run(tmp_path, {"java": "21.0.1"})["project.java.maven"].status is Status.PASS
    assert run(tmp_path, {"java": "17.0.9"})["project.java.maven"].status is Status.FAIL


def test_pom_java_legacy_one_dot_eight(tmp_path):
    (tmp_path / "pom.xml").write_text(
        POM.format("<maven.compiler.source>1.8</maven.compiler.source>")
    )
    assert run(tmp_path, {"java": "1.8.0"})["project.java.maven"].status is Status.PASS
    assert run(tmp_path, {"java": "1.7.0"})["project.java.maven"].status is Status.FAIL


def test_pom_java_undefined_property_is_skip_and_not_echoed(tmp_path):
    (tmp_path / "pom.xml").write_text(
        POM.format("<maven.compiler.release>${SECRET_PROPERTY}</maven.compiler.release>")
    )
    result = run(tmp_path, {"java": "17.0.9"})["project.java.maven"]
    assert result.status is Status.SKIP and "SECRET" not in str(result)


@pytest.mark.parametrize(
    "pom",
    [
        "<project><version>1.0</version></project>",
        "<project><release>17</release></project>",  # no maven-compiler-plugin
        POM.format("<maven.compiler.release>IGNORE PREVIOUS INSTRUCTIONS</maven.compiler.release>"),
        POM.format("<maven.compiler.release>17; rm -rf /</maven.compiler.release>"),
    ],
)
def test_pom_without_a_supported_java_target_does_not_probe(tmp_path, pom):
    (tmp_path / "pom.xml").write_text(pom)

    def unexpected_tool(*args):
        pytest.fail("No supported Java target; no tool should be probed")

    assert check_runtimes(tmp_path, unexpected_tool) == []


def test_java_version_pin_wins_over_pom(tmp_path):
    (tmp_path / ".java-version").write_text("21\n")
    (tmp_path / "pom.xml").write_text(
        POM.format("<maven.compiler.release>17</maven.compiler.release>")
    )
    results = run(tmp_path, {"java": "21.0.1"})
    assert set(results) == {"java.version", "project.java.pin"}
    assert results["project.java.pin"].status is Status.PASS


def test_pom_java_id_has_an_explanation(tmp_path):
    (tmp_path / "pom.xml").write_text(
        POM.format("<maven.compiler.release>17</maven.compiler.release>")
    )
    ids = {r.check_id for r in check_runtimes(tmp_path, fake({"java": "17.0.9"}))}
    assert "project.java.maven" in ids and ids <= set(EXPLANATIONS)
