"""Local JSON intake commands; output never logs complete project records."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .catalog import Catalog
from .errors import ContractError
from .intake import IntakeSession
from .local_files import Workspace
from .serialization import dumps, loads


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default embeds user arguments/paths in diagnostic text.
        raise ContractError("CLI_ARGUMENT_ERROR")


def _parser():
    parser = _Parser(description="光伏私有本地资料与计算契约 / local intake and calculation contracts；资料收集阶段不计算、不联网；契约导出不运行项目。",
                     epilog="KNOWN_LIMIT：不是操作系统沙箱；Windows无openat/强制目录隔离，目录竞态仍有边界。仅供私有本地目录；ACL由用户管理，不得作为公开不可信服务。")
    parser.add_argument("--workspace", required=True, help="已存在的授权私有目录；JSON路径均相对此目录")
    parser.add_argument("--baseline-dir", help="冻结基线目录；源码默认docs/solar-pv，安装后可显式提供")
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="新建项目，不覆盖已有文件")
    new.add_argument("--project-id", required=True)
    new.add_argument("--pv-type", required=True)
    new.add_argument("--state", required=True)
    status = commands.add_parser("status", help="只读revision、输入成熟度和下一轮问题")
    status.add_argument("--state", required=True)
    export = commands.add_parser("export", help="完整数据仅写入指定私有JSON文件；不覆盖")
    export.add_argument("--state", required=True)
    export.add_argument("--output", required=True)
    formula = commands.add_parser("formula", help="查询冻结公式定义、变量及输入缺口；不执行计算")
    formula.add_argument("--formula-id", required=True)
    formula.add_argument("--state", help="可选私有项目JSON；省略时不评价是否缺数据")
    formula.add_argument("--output", help="完整定义和实例元数据写私有JSON，不覆盖；stdout只输出摘要")
    for name in ("calculation-schema", "method-schema", "calculation-formulas"):
        contract = commands.add_parser(name, help="导出版本化计算契约或真实公式执行库存；不运行项目、不升级门禁")
        contract.add_argument("--output", required=True, help="授权私有JSON输出，不覆盖")
    energy = commands.add_parser("energy", help="Phase3B离线发电计算；不计算负荷、收入或财务")
    energy.add_argument("--input", required=True, help="Phase2完整导出JSON")
    energy.add_argument("--methods", required=True, help="D2方法配置JSON")
    energy.add_argument("--budget", required=True, help="显式D3预算JSON")
    energy.add_argument("--bundle", help="已授权私有目录内的D3时序bundle")
    energy.add_argument("--output", required=True, help="新建的私有结果目录，不覆盖")
    consumption = commands.add_parser("consumption", help="Phase3C消纳及售电收益；只消费已验证3B输出，不计算财务")
    consumption.add_argument("--input", required=True, help="Phase2完整结算输入导出JSON")
    consumption.add_argument("--methods", required=True, help="D2明确方法/假设配置JSON")
    consumption.add_argument("--budget", required=True, help="显式D3预算JSON")
    consumption.add_argument("--generation", required=True, help="workspace内已有3B结果目录")
    consumption.add_argument("--generation-hash", required=True, help="调用方固定的3B结果内容SHA-256，不自动信任另一目录")
    consumption.add_argument("--bundle", help="workspace内D3负荷/市场价时序目录")
    consumption.add_argument("--output", required=True, help="新建私有结果目录，不覆盖")
    financial = commands.add_parser("financial", help="Phase3D成本、资产、融资、税费及财务基础账簿；不组装Phase3E现金流")
    financial.add_argument("--input", required=True, help="包含Phase3D冻结财务输入的Phase2完整导出JSON")
    financial.add_argument("--methods", required=True, help="包含已批准Phase3D账簿参数的D2方法配置JSON")
    financial.add_argument("--settlement", required=True, help="已验收Phase3C结果目录或result.json")
    financial.add_argument("--output", required=True, help="新建私有结果目录，不覆盖")
    phase3e = commands.add_parser("phase3e", help="Phase3E冻结财务评价；消费Phase3D账簿并按公式逐项输出项目级状态")
    phase3e.add_argument("--input", required=True, help="包含Phase3D冻结财务输入的Phase2完整导出JSON")
    phase3e.add_argument("--methods", required=True, help="包含已批准D2方法参数的JSON")
    phase3e.add_argument("--settlement", required=True, help="已验收Phase3C结果目录或result.json")
    phase3e.add_argument("--output", required=True, help="新建私有结果目录，不覆盖")
    for command in ("submit", "revise", "resolve", "review", "remove", "accept"):
        examples = {
            "submit": '{"submission_id":"round1","updates":[{"field_id":"site.total_area","value":1000,"unit":"m2"}]}',
            "revise": 'submission_id, updates, reason（非空修订原因）',
            "resolve": 'submission_id, field_id, candidate_id, reviewer, reason',
            "review": 'submission_id, field_id, reviewer, reason, license_status="AUTHORIZED"',
            "remove": 'submission_id, field_ids（数组）, reason',
            "accept": '{"submission_id":"accept1","parsed_file":"parsed.json","indices":[0]}；索引从0开始，只确认选中候选，不核实真实性',
        }
        operation = commands.add_parser(command, help="独立事务；JSON含submission_id，revise/remove须reason", epilog=examples[command])
        operation.add_argument("--state", required=True)
        operation.add_argument("--input", required=True, help="JSON packet；未知键拒绝；数字更新须显式unit")
        operation.add_argument("--expected-revision", required=True, type=int)
    parse = commands.add_parser("parse", help="只解析附件候选，不修改项目；PARTIAL退出3，NEEDS_OCR退出4")
    parse.add_argument("--attachment", required=True, help="附件路径；相对路径以input-root为基准")
    parse.add_argument("--input-root", required=True, help="显式授权附件根目录；相对路径以workspace为基准")
    parse.add_argument("--output", required=True, help="候选JSON私有输出；不覆盖")
    parse.add_argument("--encoding", default="utf-8-sig", help="文本显式编码，默认utf-8-sig；不猜测")
    return parser


def _summary(result):
    maturity = result["maturity"]
    return {"revision": result["revision"], "duplicate": result.get("duplicate", False),
            "maturity": {"current_level": maturity["current_level"], "qualified_level": maturity["qualified_level"],
                         "level_scope": "INPUT_EVIDENCE_ONLY", "calculation_status": "NOT_IMPLEMENTED"},
            "next_questions": maturity["next_questions"]}


def _apply(session, command, packet, revision, workspace):
    required = {
        "submit": {"submission_id", "updates"},
        "revise": {"submission_id", "updates", "reason"},
        "resolve": {"submission_id", "field_id", "candidate_id", "reviewer", "reason"},
        "review": {"submission_id", "field_id", "reviewer", "reason", "license_status"},
        "remove": {"submission_id", "field_ids", "reason"},
        "accept": {"submission_id", "parsed_file", "indices"},
    }[command]
    allowed = required | {"action"} | ({"reason"} if command == "submit" else set())
    if (not isinstance(packet, dict) or not required <= packet.keys() or packet.keys() - allowed
            or ("action" in packet and packet["action"] != command)):
        raise ContractError("INVALID_COMMAND_PACKET")
    kwargs = {key: value for key, value in packet.items() if key != "action"}
    if command == "accept":
        if not isinstance(kwargs["parsed_file"], str) or not kwargs["parsed_file"]:
            raise ContractError("INVALID_COMMAND_PACKET")
        parsed, _ = workspace.read(kwargs.pop("parsed_file"))
        if not isinstance(parsed, dict):
            raise ContractError("INVALID_COMMAND_PACKET")
        return session.accept_candidates(**kwargs, parsed=parsed, expected_revision=revision)
    return getattr(session, command)(**kwargs, expected_revision=revision)


def _parse(args, workspace, catalog):
    from .parsers import parse_attachment

    output = workspace.path(args.output)
    if output.exists():
        raise ContractError("OUTPUT_EXISTS")
    input_root = workspace.root / Path(args.input_root)
    attachment = input_root / Path(args.attachment)
    parsed = parse_attachment(attachment, input_root, catalog=catalog, work_root=workspace.root, encoding=args.encoding)
    workspace.create(args.output, parsed)
    print(dumps({"status": parsed["status"], "candidate_count": len(parsed["candidates"]),
                 "quality_notes": parsed["quality_notes"], "calculation_status": "NOT_IMPLEMENTED"}))
    if parsed["status"] in {"FAILED", "BLOCKED"}:
        raise ContractError((parsed.get("error") or {}).get("code", "ATTACHMENT_PARSE_FAILED"))
    if parsed["status"] == "NEEDS_OCR":
        return 4
    return 0 if parsed["status"] == "PARSED" and parsed["candidates"] else 3


def main(argv=None):
    catalog = None
    try:
        args = _parser().parse_args(argv)
        workspace = Workspace(args.workspace)
        catalog = Catalog(args.baseline_dir)
        if args.command == "consumption":
            from contextlib import nullcontext
            from .timeseries_bundle import BundleBudget, read_bundle
            from .calculation.revenue import calculate_rooftop, calculate_ground
            from .calculation.method_config import MethodConfig
            exported = workspace.read(args.input)[0]
            methods = MethodConfig.from_dict(workspace.read(args.methods)[0])
            budget_data = workspace.read(args.budget)[0]
            if not isinstance(budget_data, dict):
                raise ContractError("BUNDLE_BUDGET")
            budget = BundleBudget(**budget_data)
            pv_type = exported.get("project", {}).get("pv_type")
            if pv_type not in {"industrial_rooftop", "utility_scale_ground"}:
                raise ContractError("CONSUMPTION_CATEGORY_NOT_IMPLEMENTED")
            calculate = calculate_rooftop if pv_type == "industrial_rooftop" else calculate_ground
            context = read_bundle(workspace.path(args.bundle,json_only=False),catalog=catalog,budget=budget) if args.bundle else nullcontext(None)
            with context as bundle:
                result = calculate(exported,methods,catalog=catalog,budget=budget,bundle=bundle,
                    generation_dir=workspace.path(args.generation,json_only=False),generation_result_hash=args.generation_hash,
                    output_dir=workspace.path(args.output,json_only=False))
            print(dumps({"status":result["status"],"result_hash":result["result_hash"],
                "calculation_maturity":result["maturity"]["calculation"],"scope":"PHASE3C_CONSUMPTION_AND_ENERGY_BENEFIT_ONLY"}))
            return 0
        if args.command == "financial":
            from .calculation.financial_ledger import calculate_financial_ledger, write_financial_bundle
            from .calculation.method_config import MethodConfig
            from .calculation.result_contract import validate_result
            exported = workspace.read(args.input)[0]
            methods = MethodConfig.from_dict(workspace.read(args.methods)[0])
            settlement_path = workspace.path(args.settlement, json_only=False)
            if settlement_path.is_dir(): settlement_path = settlement_path / "result.json"
            settlement = loads(settlement_path.read_bytes())
            result = calculate_financial_ledger(exported, methods, settlement, catalog=catalog)
            validate_result(result, catalog)
            write_financial_bundle(result, workspace.path(args.output, json_only=False))
            print(dumps({"status":result["status"],"result_hash":result["result_hash"],"calculation_maturity":result["maturity"]["calculation"],"scope":"PHASE3D_FINANCIAL_FOUNDATION_ONLY","phase3e":"NOT_IMPLEMENTED"}))
            return 0
        if args.command == "phase3e":
            from .calculation.financial_ledger import calculate_financial_ledger
            from .calculation.phase3e import calculate_phase3e, write_phase3e_bundle
            from .calculation.method_config import MethodConfig
            from .calculation.result_contract import validate_result
            exported = workspace.read(args.input)[0]
            methods = MethodConfig.from_dict(workspace.read(args.methods)[0])
            settlement_path = workspace.path(args.settlement, json_only=False)
            if settlement_path.is_dir(): settlement_path = settlement_path / "result.json"
            settlement = loads(settlement_path.read_bytes())
            foundation = calculate_financial_ledger(exported, methods, settlement, catalog=catalog)
            result = calculate_phase3e(foundation, methods, catalog)
            validate_result(result, catalog)
            write_phase3e_bundle(result, workspace.path(args.output, json_only=False))
            print(dumps({"status": result["status"], "result_hash": result["result_hash"],
                         "calculation_maturity": result["maturity"]["calculation"],
                         "scope": "PHASE3E_FROZEN_FINANCIAL_EVALUATION", "instantaneous_payment_coverage": "INDETERMINATE"}))
            return 0
        if args.command == "energy":
            from contextlib import nullcontext
            from .timeseries_bundle import BundleBudget, read_bundle
            from .calculation.energy_yield import calculate_rooftop, calculate_ground
            from .calculation.method_config import MethodConfig
            exported = workspace.read(args.input)[0]
            methods = MethodConfig.from_dict(workspace.read(args.methods)[0])
            budget_data = workspace.read(args.budget)[0]
            if not isinstance(budget_data, dict):
                raise ContractError("BUNDLE_BUDGET")
            budget = BundleBudget(**budget_data)
            pv_type = exported.get("project", {}).get("pv_type")
            if pv_type not in {"industrial_rooftop", "utility_scale_ground"}:
                raise ContractError("ENERGY_CATEGORY_NOT_IMPLEMENTED")
            calculate = calculate_rooftop if pv_type == "industrial_rooftop" else calculate_ground
            context = read_bundle(workspace.path(args.bundle, json_only=False), catalog=catalog, budget=budget) if args.bundle else nullcontext(None)
            with context as bundle:
                result = calculate(exported, methods, catalog=catalog, budget=budget,
                                   output_dir=workspace.path(args.output, json_only=False), bundle=bundle)
            print(dumps({"status": result["status"], "result_hash": result["result_hash"],
                         "calculation_maturity": result["maturity"]["calculation"], "scope": "PHASE3B_ENERGY_ONLY"}))
            return 0
        if args.command in {"calculation-schema", "method-schema", "calculation-formulas"}:
            if args.command == "calculation-formulas":
                from .calculation.execution_registry import execution_inventory
                inventory = execution_inventory(catalog)
                workspace.create(args.output, {"definition_version": catalog.definition_version,
                                              "definition_hash": catalog.definition_hash, "formulas": inventory})
                print(dumps({"status": "CONTRACT_EXPORTED", "formula_count": len(inventory),
                             "implemented_tested": sum(row["status"] == "IMPLEMENTED_TESTED" for row in inventory),
                             "scope": "EVIDENCE_BACKED_REGISTRY_NOT_PROJECT_COMPUTATION"}))
            else:
                if args.command == "calculation-schema":
                    from .calculation.result_contract import result_schema
                    schema = result_schema()
                else:
                    from .calculation.method_config import method_schema
                    schema = method_schema()
                workspace.create(args.output, schema)
                print(dumps({"status": "CONTRACT_EXPORTED", "schema_version": schema["$id"],
                             "numerical_validation": "NOT_PERFORMED_BY_THIS_COMMAND"}))
            return 0
        if args.command == "formula":
            from .formula_bindings import FormulaBindings
            project = IntakeSession.from_dict(workspace.read(args.state)[0], catalog).project if args.state else None
            query = FormulaBindings(catalog).describe(args.formula_id, project)
            if args.output:
                workspace.create(args.output, query)
            keys = ("formula_id", "name_zh", "input_presence_evaluated", "missing_input_field_ids",
                    "missing_variable_field_ids", "uncomputed_formula_field_ids", "unverified_constant_field_ids",
                    "calculation_status", "can_execute_calculation")
            print(dumps({key: query[key] for key in keys}))
            return 0
        if args.command == "parse":
            return _parse(args, workspace, catalog)
        if args.command == "new":
            session = IntakeSession.new(args.project_id, args.pv_type, catalog)
            workspace.create(args.state, session.project.to_dict())
        elif args.command in {"status", "export"}:
            state, _ = workspace.read(args.state)
            session = IntakeSession.from_dict(state, catalog)
            if args.command == "export":
                workspace.create(args.output, session.export())
        else:
            packet, _ = workspace.read(args.input)
            with workspace.lock(args.state):
                state, previous_digest = workspace.read(args.state)
                session = IntakeSession.from_dict(state, catalog)
                result = _apply(session, args.command, packet, args.expected_revision, workspace)
                if not result["duplicate"]:
                    workspace.replace(args.state, session.project.to_dict(), previous_digest)
                print(dumps(_summary(result)))
                return 0
        print(dumps(_summary(session.status())))
        return 0
    except ContractError as exc:
        # Only catalog field identifiers may leave the boundary, never raw paths.
        field = exc.field_id if catalog is not None and isinstance(exc.field_id, str) and exc.field_id in catalog.fields else None
        print(dumps({"error": {"code": exc.code, "field_id": field}}), file=sys.stderr)
        return 2
    except FileNotFoundError:
        print('{"error":{"code":"FILE_NOT_FOUND","field_id":null}}', file=sys.stderr)
        return 2
    except PermissionError:
        print('{"error":{"code":"LOCAL_PERMISSION_DENIED","field_id":null}}', file=sys.stderr)
        return 2
    except OSError:
        print('{"error":{"code":"LOCAL_IO_ERROR","field_id":null}}', file=sys.stderr)
        return 2
    except Exception:
        print('{"error":{"code":"LOCAL_OPERATION_FAILED","field_id":null}}', file=sys.stderr)
        return 2
