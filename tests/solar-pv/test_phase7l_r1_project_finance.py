"""The two ordinary CLI ingress parsers forward terminal source paths."""


def test_project_cli_accepts_source_and_exact_document_path():
    from wangbin_solar_pv.cli import _parser
    parsed = _parser().parse_args(["--workspace", "private", "project", "--input", "input.json",
        "--methods", "methods.json", "--bundle", "bundle", "--budget", "budget.json",
        "--output", "project", "--terminal-source", "terminal.json",
        "--terminal-document", "terminal.txt"])
    assert (parsed.terminal_source, parsed.terminal_document) == ("terminal.json", "terminal.txt")


def test_project_report_wrapper_accepts_terminal_paths():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "packages/skills/wangbin-solar-pv-prestudy/scripts/run_solar_pv.py"
    spec = importlib.util.spec_from_file_location("solar_pv_project_report_wrapper", path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    parsed = wrapper._parser().parse_args(["project-report", "--project-type", "industrial_rooftop",
        "--workspace", "private", "--terminal-source", "terminal.json", "--terminal-document", "terminal.txt"])
    assert (parsed.terminal_source, parsed.terminal_document) == ("terminal.json", "terminal.txt")


def test_project_cli_accepts_optional_trading_fee_payment_source():
    from wangbin_solar_pv.cli import _parser
    base = ["--workspace", "private", "project", "--input", "input.json",
            "--methods", "methods.json", "--bundle", "bundle", "--budget", "budget.json",
            "--output", "project"]
    assert _parser().parse_args(base).trading_fee_payment_source is None
    assert _parser().parse_args(base + ["--trading-fee-payment-source", "fee.json"]).trading_fee_payment_source == "fee.json"


def test_project_report_forwards_only_explicit_safe_trading_fee_source(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    import pytest

    path = Path(__file__).resolve().parents[2] / "packages/skills/wangbin-solar-pv-prestudy/scripts/run_solar_pv.py"
    spec = importlib.util.spec_from_file_location("solar_pv_project_report_wrapper", path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    monkeypatch.setattr(wrapper, "_engine", lambda _: (tmp_path, tmp_path, tmp_path))
    calls = []
    monkeypatch.setattr(wrapper, "_engine_command", lambda *args: calls.append(args) or {"status": "BLOCKED"})
    base = ["project-report", "--project-type", "industrial_rooftop", "--workspace", str(tmp_path),
            "--input", "input.json", "--methods", "methods.json", "--bundle", "bundle",
            "--budget", "budget.json", "--project-output", "project", "--report-output", "report"]
    assert wrapper._project_report(wrapper._parser().parse_args(base))["status"] == "BLOCKED"
    assert "--trading-fee-payment-source" not in calls[-1][-1]
    assert wrapper._project_report(wrapper._parser().parse_args(base + ["--trading-fee-payment-source", "fee.json"]))["status"] == "BLOCKED"
    assert calls[-1][-1][-2:] == ["--trading-fee-payment-source", "fee.json"]
    with pytest.raises(wrapper.WrapperError) as error:
        wrapper._project_report(wrapper._parser().parse_args(base + ["--trading-fee-payment-source", "../fee.json"]))
    assert error.value.code == "PATH_BOUNDARY"
    assert len(calls) == 2


def test_project_cli_passes_bounded_raw_trading_fee_bytes_only_when_opted_in(tmp_path, monkeypatch, capsys):
    from wangbin_solar_pv.cli import main
    from wangbin_solar_pv.calculation import project_runner

    captured = []
    def fake_run_project(*args, **kwargs):
        captured.append(kwargs["trading_fee_source_bytes"])
        return {"status": "PARTIAL", "canonical_result_hash": "hash", "receipt_hash": "receipt"}
    monkeypatch.setattr(project_runner, "run_project", fake_run_project)
    for filename in ("input.json", "methods.json", "budget.json"):
        (tmp_path / filename).write_text("{}", encoding="utf-8")
    (tmp_path / "bundle").mkdir()
    base = ["--workspace", str(tmp_path), "project", "--input", "input.json",
            "--methods", "methods.json", "--bundle", "bundle", "--budget", "budget.json",
            "--output", "project"]
    assert main(base) == 0
    assert captured == [None]
    source = tmp_path / "fee.json"
    raw = b'{}' + b' ' * (64 * 1024 - 2)
    source.write_bytes(raw)
    assert main(base + ["--trading-fee-payment-source", "fee.json"]) == 0
    assert captured == [None, raw]
    source.write_bytes(raw + b' ')
    assert main(base + ["--trading-fee-payment-source", "fee.json"]) == 2
    assert 'TRADING_FEE_SOURCE_SIZE_LIMIT' in capsys.readouterr().err
    assert captured == [None, raw]
    assert main(base + ["--trading-fee-payment-source", "../fee.json"]) == 2
    assert captured == [None, raw]
