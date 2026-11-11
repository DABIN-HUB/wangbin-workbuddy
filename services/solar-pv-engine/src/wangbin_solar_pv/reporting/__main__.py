"""Separate opt-in chapter CLI; the legacy report/ground-report are unchanged."""
import argparse
from pathlib import Path

from ..catalog import Catalog
from ..errors import ContractError
from ..local_files import Workspace
from ..report_export import ReportModel
from ..serialization import dumps
from .chapter_registry import Registry
from .chapter_result_schema import evidence_schema, result_schema
from .chapter_writer import accept, prepare, resume
from .llm_provider import ModelConfig, integration_status
from .report_assembler import assemble_chapter
from .report_planner import plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['spec-check', 'schema', 'plan', 'status', 'prepare', 'accept', 'resume'])
    parser.add_argument('--canonical', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--run')
    parser.add_argument('--chapter')
    parser.add_argument('--request-id')
    parser.add_argument('--response', help='JSON file relative to the selected run directory')
    parser.add_argument('--model')
    parser.add_argument('--reasoning-level', default='provider_default')
    parser.add_argument('--timeout-seconds', type=int, default=300)
    parser.add_argument('--max-request-bytes', type=int, default=524288)
    parser.add_argument('--max-output-bytes', type=int, default=131072)
    parser.add_argument('--max-attempts', type=int, default=2)
    parser.add_argument('--max-requests', type=int, default=24)
    parser.add_argument('--authorized-source', action='append', default=[])
    parser.add_argument('--docx', help='New DOCX filename inside selected run; partial review only')
    args = parser.parse_args(argv)
    try:
        if args.command == 'status':
            print(dumps(integration_status()))
            return 3
        catalog = Catalog()
        registry = Registry(catalog)
        if args.command in {'spec-check', 'schema', 'plan'}:
            result = {'chapter_result': result_schema(), 'evidence_pack': evidence_schema()} if args.command == 'schema' else plan(registry) if args.command == 'plan' else {
                'status': 'REQUIREMENTS_FROZEN', 'spec_hash': registry.hash,
                'counts': registry.spec['protected_counts']}
        else:
            if not all((args.canonical, args.workspace, args.run, args.model)):
                raise ContractError('CHAPTER_ARGUMENTS_REQUIRED')
            canonical = args.canonical.absolute()
            result_data, _ = Workspace(canonical.parent).read(canonical.name)
            model = ReportModel.from_result(result_data, catalog)
            workspace = Workspace(args.workspace)
            config = ModelConfig(args.model, args.reasoning_level, args.timeout_seconds,
                                 args.max_request_bytes, args.max_output_bytes, args.max_attempts, args.max_requests)
            config.to_dict()
            if args.command == 'prepare':
                result = prepare(workspace, args.run, model, registry, args.chapter, config, args.authorized_source)
                result = {k: result[k] for k in ('request_id', 'request_hash', 'generation_run_id', 'execution_state')}
            else:
                store = Workspace(workspace.path(args.run, json_only=False))
                if args.command == 'accept':
                    response, _ = store.read(args.response)
                    accepted = accept(store, args.request_id, response, model, registry, config)
                else:
                    accepted, _ = resume(store, args.request_id, model, registry, config)
                result = {k: v for k, v in accepted.items() if k != 'output'}
                if args.docx:
                    result['artifact'] = assemble_chapter(store, args.request_id, model, registry, config, args.docx)
        print(dumps(result))
        return 0
    except ContractError as exc:
        print(dumps({'status': 'BLOCKED', 'code': exc.code}))
        return 2
    except (OSError, ValueError, KeyError, TypeError):
        print(dumps({'status': 'BLOCKED', 'code': 'CHAPTER_LOCAL_IO_OR_CONTRACT'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
