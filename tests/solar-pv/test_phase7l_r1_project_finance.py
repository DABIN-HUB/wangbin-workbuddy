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
