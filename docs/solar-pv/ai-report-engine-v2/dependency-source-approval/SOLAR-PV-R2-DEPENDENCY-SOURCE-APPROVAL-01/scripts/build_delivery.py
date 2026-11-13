"""Create bounded documentation/derived plans only; never network, install or seal."""
import argparse
import csv
import importlib.util
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('locktool', HERE / 'locktool.py')
lock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lock)
R = HERE.parents[5]
# Resolve repository from the explicit marker rather than the user's home.
while not (R / 'AGENTS.md').is_file():
    if R.parent == R:
        raise RuntimeError('REPOSITORY_ROOT_NOT_FOUND')
    R = R.parent
U = R / lock.U
D = HERE.parent
C = U / 'candidate'


def load(p):
    return json.loads(p.read_bytes())


def ident(p):
    b = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'bytes': len(b), 'sha256': lock.digest(b)}


def put(p, value):
    b = value.encode('utf8') if isinstance(value, str) else lock.encoded(lock.clean(value))
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)


def ref(p):
    i = ident(p)
    return f"`{i['path']}` ({i['bytes']} B, SHA-256 `{i['sha256']}`)"


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|'] + [
        '| ' + ' | '.join(str(x).replace('|', '/').replace('\n', '<br>') for x in row) + ' |' for row in rows]) + '\n'


def main():
    value = load(C / 'CANDIDATE_LOCK.full.json')
    assert not lock.validate(value, U / 'frozen-inputs.json')
    source = U / 'source-research'
    license_dir = U / 'license-identity'
    license = load(license_dir / 'license-matrix.json')
    resources = load(license_dir / 'external-resource-plan.json')
    summary = load(source / 'shared/resolution-summary.json')
    # Large generated matrices remain ignored, with concise tracked identity manifests.
    for name, original in [('dependency-source-index.json', source / 'shared/dependency-source-matrix.json'),
                           ('dependency-compatibility-matrix.json', source / 'shared/dependency-compatibility-matrix.json'),
                           ('dependency-license-matrix.json', license_dir / 'license-matrix.json')]:
        put(C / name, {'schema': 'bound-evidence-reference/1', 'source': ident(original), 'classification': 'REFERENCE_NOT_DUPLICATED_RAW'})
    plans = []
    first_id = value['conditional_first_target']
    for fid, f in sorted(value['files'].items(), key=lambda row: row[1]['filename']):
        obligations = next(v for d in license['dependencies'] if d['name'] == f['name'] for v in d['versions'] if v['version'] == f['version'])
        plans.append({'file_id': fid, **{k: f[k] for k in ['name', 'version', 'filename', 'url', 'sha256', 'size', 'tags', 'targets', 'official_source']},
                      'stage': 'FIRST_CONDITIONAL_TARGET_CANDIDATE' if first_id in f['targets'] else 'ADDITIONAL_TARGET_ONLY',
                      'authorization': 'NOT_AUTHORIZED', 'action': 'FUTURE_APPROVAL_RECORD_ONLY_NO_EXECUTABLE_DOWNLOAD',
                      'artifact_acquired': False, 'actual_hash_verified': False, 'license_review': 'BLOCKED',
                      'license_text_status': obligations['source_text_status'], 'notice_conditions': obligations['obligations'],
                      'binary_notice_conditions': obligations['bundled_review'], 'next_evidence': obligations['required_next_evidence']})
    download = {'schema': 'controlled-future-acquisition-plan/1', 'status': 'PROPOSED_NOT_INSTALLABLE',
                'identity_rule': 'exact filename + official SHA256 + exact official URL',
                'counts': value['counts'], 'files': plans, 'targets': [
                    {'target': t['id'], 'file_ids': [n['file_id'] for n in t['nodes'] if n['file_id']],
                     'gaps': [n for n in t['nodes'] if n['gap']], 'approval': 'PENDING', 'closure': 'BLOCKED'} for t in value['targets']],
                'excluded': ['YANKED pypdfium2==5.15.1', 'internal document wheel: unresolved dual SHA', 'backends are not runtime acquisitions'],
                'no_network_or_installer_code': True}
    put(C / 'download-plan.json', download)
    put(C / 'first-target-exact-files.json', {'target': first_id, 'status': 'CONDITIONAL_NOT_FORMAL_NOT_COMPLETE',
                                               'files': [p for p in plans if first_id in p['targets']],
                                               'gaps': [n for n in value['targets'][0]['nodes'] if n['gap']],
                                               'internal': {'solar': value['root_artifact'], 'document': value['document_cli_identity']}})
    put(C / 'dependency-resolution.full.json', {'schema': 'official-metadata-resolution/1', 'counts': value['counts'],
                                                  'targets': value['targets'], 'metadata_variants': value['metadata_variants'],
                                                  'source': ident(source / 'shared/dependency-edges.json')})
    # Formal lock is the small, identity-bearing entry point to the full ignored machine candidate.
    put(D / 'CANDIDATE_LOCK.json', {'schema': 'solar-pv-candidate-lock-manifest/1', 'status': value['status'],
                                    'dependency_closure': 'BLOCKED', 'source_head': lock.BASE,
                                    'full_candidate': ident(C / 'CANDIDATE_LOCK.full.json'),
                                    'input_capsule': {'path': lock.U + 'frozen-inputs.json', 'sha256': lock.ANCHOR_SHA, 'sharing': 'LOCAL_ONLY'},
                                    'counts': value['counts'], 'node_versions': sorted(value['nodes']),
                                    'targets': [{'id': t['id'], 'files': sum(n['file_id'] is not None for n in t['nodes']),
                                                 'gaps': [n['key'] for n in t['nodes'] if n['gap']], 'closure': 'BLOCKED'} for t in value['targets']],
                                    'download_plan': ident(C / 'download-plan.json'),
                                    'first_target_exact_files': ident(C / 'first-target-exact-files.json'),
                                    'schema_description': 'full_candidate contains input identities, 43 nodes, metadata variants, all declared/active edges and extras/markers for 12 targets, 115 files with URL/SHA/tags/license/chains; this manifest is not an installer lock',
                                    'validator': 'scripts/locktool.py validate --inputs <local frozen-inputs.json> --candidate <full_candidate.path>',
                                    'qa': 'PENDING_INDEPENDENT_QA'})
    put(D / 'DEPENDENCY_RESOLUTION.json', {'schema': 'dependency-resolution-manifest/1', 'status': 'METADATA_FIXED_POINT_COMPLETE_NOT_ARTIFACT_CLOSURE',
                                           'dependency_closure': 'BLOCKED', 'counts': summary['counts'], 'targets': summary['targets'],
                                           'recomputed_resolution': ident(C / 'dependency-resolution.full.json'),
                                           'official_edges_original': ident(source / 'shared/dependency-edges.json'),
                                           'marker_clarification': ident(source / 'shared/MARKER_COMPARISON_CLARIFICATION.json') if (source / 'shared/MARKER_COMPARISON_CLARIFICATION.json').exists() else ident(source / 'MARKER_COMPARISON_CLARIFICATION.json'),
                                           'source_sharing_index': ident(source / 'sharing-index.final.json'),
                                           'license_matrix': ident(license_dir / 'license-matrix.json')})
    # Required 504-row formal CSV is useful audit contract, not the raw API catalog.
    text = (source / 'shared/DEPENDENCY_SOURCE_MATRIX.csv').read_text(encoding='utf8')
    put(D / 'DEPENDENCY_SOURCE_MATRIX.csv', text)
    put(D / '.gitattributes', '# Task-local immutable evidence/document bytes only.\n* -text\nscripts/* -text\n')
    versions = [(n['name'], n['version'], n['source'], n['license_text_status'], 'BLOCKED') for n in value['nodes'].values()]
    put(D / 'RESULT.md', '''# 依赖来源审核结果（候选冻结，待独立 QA）

结论：**SOURCE_RESEARCH_COMPLETE / ARTIFACT_ACQUISITION_NOT_AUTHORIZED / DEPENDENCY_CLOSURE_BLOCKED**。
数据完整性自检与可分发性是两个门禁；来源已研究不意味着可安装或许可放行。

- 十二旧图各 42 个第三方名称，合并 42 名称 / 43 精确版本；tzdata 在 Windows 为 2026.5，其余目标为 2026.6。
- 43/43 官方精确版本 JSON HTTP 200；另列 2 个 backend，不混入 runtime42。
- 官方记录 926 个 runtime wheel 文件摘要；本提案选择 115 唯一非撤回候选（34 pure、81 平台专属），486 个目标分配、18 缺口。
- 第三方实际 wheel 取得 0，实际 wheel SHA 验证 0；121 个 `.whl.metadata` 是元数据，不是 wheel，PEP658 索引期望摘要未核。
- 许可证工程初审 42 名称/43版本；39名称/40版本取得精确 tag 许可文本，但 tag-to-wheel 未证。所有 42 名称再分发仍 BLOCKED。
- pypdfium2 5.15.1 全部目标撤回拒绝；macOS x86_64 另缺 cryptography 50.0.2、onnxruntime 1.31.1。没有自动升级或允许 yanked。
- 正式首目标 UNCONFIRMED；建议仅条件研究 Windows AMD64 / 标准 GIL CPython 3.12，41 候选 + 1 缺口 + 两个 internal，尚非可安装集合。
- document-cli 1.2.0 双 SHA 不能自动择一；12 外置 baseline、11 可选 fixture、历史五回执/四输入不完整重放问题保留。

## 文件导航

`CANDIDATE_LOCK.json`、`DEPENDENCY_RESOLUTION.json` 是小型正式身份清单，精确绑定 RUN/candidate 内完整机器锁/图/下载计划；大 JSON、raw、日志、输入胶囊只留忽略目录，不入 Git。
完整锁包含 43 节点/12 targets/全部声明边及 marker/extras/115 文件/URL/SHA/tags/许可状态/所属父链和取得状态，不是空占位。
首目标逐项文件表见 WHEELHOUSE_AND_INSTALL_PLAN.md；504 行跨平台表见 DEPENDENCY_SOURCE_MATRIX.csv。

开发自检与提交/冻结索引的最终实数在 RUN/developer-final-state.json 和 RUN/developer-freeze-index.json；文档不嵌入自身未来 commit SHA。
QUALITY_REPORT.md 目前是审核入口和待验清单，不是作者自签独立 QA。没有封 ZIP；下一轮独立 QA 后的文档收口和分享 payload 还需限定复审。

## 43 精确发行来源

''' + table(['包','版本','官方来源','许可文本 scope','再分发'], versions) + '\n来源原证：' + ref(source / 'sharing-index.final.json') + '\n')
    root = value['root_artifact']
    resource_rows = [(b['path'], b['bytes'], b['sha256'], b['future_relative_path']) for b in resources['external_baselines']]
    optional = [(b['path'], b['bytes'], b['sha256'], '非正式运行必要；SYNTHETIC；未打包') for b in resources['optional_fixtures']]
    put(D / 'BASELINE_AND_ARTIFACT_IDENTITY.md', f'''# 基线、构件与保护身份

源/文档基线 HEAD：`{lock.BASE}`，main；manager 的 remote main 只读结果与之相同，未 fetch/pull/push。
接管时 tracked diff/cached 均空，仅本任务 PLAN 未跟踪。

旧 solar wheel：{root['path']}，557392 B，SHA `{root['sha256']}`；保持不重建、不覆盖。
旧 SOURCE-REVIEW-ONLY.zip：2621668 B，SHA `fd4d52d6b6725902439779956c49b0fa8560839c562fa5ffaba605798198ae4c`。
旧 final-payload-index.json：304435 B，SHA `122400a048e9c94f84688c62f5f4a477566923c42f92bbf901f14d4b223e1c79`。

manager 已逐件绑定 129 源文件、十份旧正式文档及八核心；本轮用 manager-reused-source-document-binding.json 复用，不重做历史 wheel 审计。
保护账本 3458 文件需要末次逐 SHA 比对；installed Skill 22 文件需成员全集与逐 SHA 不变；R8–R13 的 2638 历史文件仅 size/mtime 元信息保护，不夸大为全文哈希复核。

## 12 外置必需 baseline

保持 EXTERNAL_BASELINE_RESOURCES=NOT_SELF_CONTAINED。未来经审批从批准 source commit/可信渠道只导出以下十二件，manifest 同绑 engine wheel SHA、baseline-lock raw SHA、各件 raw 与 UTF-8-sig/BOM/CRLF 规范化内容 SHA。
Catalog 构造会校验每一 lock 项；使用显式 baseline-dir，不能靠开发 checkout 静默兜底，不能修改 canonical。

''' + table(['源路径','B','raw SHA256','未来相对路径'],resource_rows) + '''
## 11 可选 fixture

OPTIONAL_DEMO_FIXTURES=NOT_BUNDLED。属于既有 synthetic/editorial/regression 数据，不是授权真实输入；正式运行不依赖这些示例。
默认 editorial fixture 在 wheel 缺失的历史问题继续披露；若后续需要，单独申请演示包和分发权，不与 required baseline 混包。

''' + table(['源路径','B','SHA256','性质'], optional) + '''
## 历史不可重放

HISTORICAL_RECEIPTS=PARTIALLY_NOT_REPLAYABLE：五条成功回执引用的四原输入不完整，不能用同名/其他版本或新值填补。原 HTTP raw 缺口也不能补造。
证据：license-identity/historical-input-identities.json；external-resource-plan.json 保存逐项 raw 与 normalized 比对及调用链。

''' + ref(license_dir / 'external-resource-plan.json') + '\n')
    rows = [(t['id'],sum(n['file_id'] is not None for n in t['nodes']),','.join(n['key'] for n in t['nodes'] if n['gap']),len([e for e in t['graph']['edges'] if e['active']]),'BLOCKED') for t in value['targets']]
    put(D / 'TARGET_RUNTIME_MATRIX.md', '''# 目标运行环境与兼容性

| 身份 | 实际证据 | 限定结论 |
|---|---|---|
| OS/client | Windows 10 10.0.19045 / AMD64 / 64bit；WorkBuddyAI 文件与真实进程 5.5.2 | 客户端存在，不证明 Python 绑定 |
| DEV | 根 .venv CPython 3.12.0，packaging 26.3 | 本次解析工具；DEV_ENV_ONLY |
| Hermes | CPython 3.14.9 | 不是 WorkBuddy interpreter |
| Skill Bash | 未获得直接解释器绑定 | UNKNOWN |
| Connector | 配置声明 Python 3.12，部署 exe 未观察 | UNKNOWN |
| 首个正式目标 | 未确认 managed interpreter | UNCONFIRMED_BLOCKED_BY_RUNTIME_IDENTITY |

以下 .0 patch 是旧 marker 环境代表值，不是部署观测。未来实际 patch 改变必须重新计算 Requires-Python/marker/tag；不能将 DEV 或声明 runtime 当实际宿主。
仅接受标准 GIL cp312/cp313/cp314 和适用旧 abi3，拒绝 t-GIL/abi3t。Linux 只条件研究 glibc/manylinux，不能混用 musl/未知 linux ABI；macOS 最低版本按每文件保留，arm64 至少 11.0，未知实际最低 OS 仍是条件。

''' + table(['原目标','候选数','缺口','活跃边','分发闭包'], rows) + '''
十二目标固定点均未发现新增缺失节点、版本冲突、Requires-Python 冲突、未定义 extra 或未知边；这只是元数据闭合，不是实际分发闭包。
官方 magika 使用 python_version，旧 installed 使用 python_full_version（含通配 patch）；声明字符串不同，但在原 12 环境的活跃包/约束求值相同，不能外推所有可能环境逻辑等价。
MARKER_COMPARISON_CLARIFICATION.json 保存澄清；原图、官方 overlay 均未改写。

参见 [官方 wheel tag 规范](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)、[PyPI JSON API](https://docs.pypi.org/api/json/)。本地五页官方 docs 全 HTTP200 身份在 manager-official-docs-index.json。
[WorkBuddy Connector](https://open.workbuddy.cn/docs/connector) 的托管环境声明与 [Skill](https://open.workbuddy.cn/docs/skill) Bash 能力需分开；不能从文档推导本机已部署、OS sandbox、资源上限或业务调用 timeout。
''' + '\n运行原证：' + ref(U / 'manager-target-runtime.json') + '\n')
    # Preserve analyst's per-item obligations verbatim; no blanket permissive-license shortcut.
    license_text = (license_dir / 'license-matrix.md').read_text(encoding='utf8')
    put(D / 'THIRD_PARTY_LICENSE_MATRIX.md', '''# 第三方许可证初审与逐项义务

审阅范围 42 名称/43精确版本；官方 tag 文本覆盖 39名称/40版本，所有再分发 BLOCKED，绝非法律 PASS。
以下引用分析员逐项义务原文，保留其 exact scope、HTTP/SHA 和差异，不用 MIT/BSD 标签替代实际许可证/NOTICE。

- beautifulsoup4：文档 title=4.14.3、body=4.15.0，不能 pin 为精确许可证据。
- cobble：0.1.4/v0.1.4 的 LICENSE/LICENSE.txt 均 404，不能据 installed 字段放行。
- protobuf：有 v36.2 LICENSE，但 7.36.2→tag/官方关联未证。
- lxml：BSD root 不覆盖 binary iconv LGPL-2.1、ElementTree/PSF、schema/XSL 等例外；实际 linking/source/relink 路径待构件与法律核查。
- Pillow 为 MIT-CMU，不是普通 MIT；certifi 的 MPL-2.0 covered-source 提供途径待核。
- cffi MIT-0、PSF 包的变更摘要、packaging/cryptography/dateutil 双许可选择需分别记录。
- numpy/onnxruntime/cryptography/pypdfium2 的 bundled/native NOTICE 需按实际平台 wheel 裁定；仓库聚合文本或 404 不证明 wheel 无 NOTICE。

这是工程尽调，商业再分发仍需权利人/法律审核。脱敏分享文本不是可直接随二进制再分发的完整 legal notice。

---

''' + license_text)
    first = [p for p in plans if first_id in p['targets']]
    filetable = table(['精确包版本','wheel 文件名','官方 SHA256','精确官方 URL','Python/ABI/platform tags'], [
        (p['name']+'=='+p['version'],p['filename'],p['sha256'],p['url'],','.join(p['tags'])) for p in first])
    put(D / 'WHEELHOUSE_AND_INSTALL_PLAN.md', '''# wheelhouse 与后续安装计划（纯文字，未执行）

## 条件首目标：Windows AMD64 / 标准 GIL CPython 3.12

此处 41 个非撤回第三方文件可供未来**分批准阶段**取证；当前均 NOT_AUTHORIZED / ARTIFACT_NOT_ACQUIRED / actual_hash_verified=false / LICENSE_REVIEW=BLOCKED。
缺失 pypdfium2==5.15.1（全撤回）；没有获准替代版本或允许撤回的审批，不得闭包 PASS。
另有 internal solar==0.3.2 已本地静态审核 wheel（不是安装通过），document==1.2.0 双 SHA 未裁定；42第三方+2internal 尚不完整。
每文件 notice/版本文本状态/后续证据在 download-plan.json；不能因 pure-any 就免除数据资源或许可审核。

''' + filetable + '''
## 十二目标去重与受控下载提案

115 唯一身份严格以 filename + SHA256 + URL 去重；34 pure、81 platform、486分配、18缺口。
全部目标所需 file_ids 与具体 gaps 在 download-plan.json.targets；全115项URL/hash/tags/目标/逐项notice条件在 files。
setuptools 84.1.0 / wheel 0.48.0 仅 backend 来源研究，既非 runtime42，也不在首目标41下载集合；动态 backend 需求未运行未知。

1. 人工先确认正式 runtime/patch/ABI/OS，并批准精确 URL/hash 列表、保存目录、体积与网络边界；许可研究不等于取得或再分发授权。
2. 若只批准首目标41件证据下载，仍标识为不完整取证批次，不进行安装；拒绝 yanked，拒绝 hash/版本/URL 不一致，拒绝静默替代。
3. 独立审批解决 pypdfium2 pin、document 双构件和三项文本缺口；任何版本调整必须新建候选图与独立复核，不能改原合同来填洞。
4. 审批后每件实际文件先计算完整 SHA256，再核安全路径/ZIP唯一成员/CRC/RECORD/元数据/各层 LICENSE/NOTICE/native来源，建立 acquired 与 actual_hash_verified 的真实回执。
5. 未通过的文件隔离，不能进 approved；hash一致仅证明身份，不等于来源签名证明或法律批准。

## 未来目录（本轮没有创建 wheelhouse）

- wheelhouse/proposed/<target>/ 仅候选 manifest，不放未获准二进制。
- wheelhouse/quarantine/<filename+sha>/ 保存获准下载待核文件与来源/时间回执。
- wheelhouse/approved/<target>/ 只收完成各门禁的不可变文件，纯Python可内容寻址复用，target manifest 显式映射。
- wheelhouse/notices/<filename+sha>/ 保留实际构件版权、许可、NOTICE 与对应源码/链接义务。
- wheelhouse/baseline/<engine-sha>/ 十二外置必需资源；optional-demo 独立审批与 SYNTHETIC 标识。

## 隔离离线安装方案（禁止本轮执行；不含可执行联网安装代码）

获得完整构件闭包/许可/资源及独立批准后，使用一个全新专用目录与已确认绝对解释器；不覆盖 DEV、全局或 WorkBuddy managed venv。
清除开发 PYTHONPATH、禁用用户 site；安装只从批准 wheelhouse，禁索引/联网/隐式依赖补装与构建，要求每项严格版本/hash约束。
预先验证全部构件与资源后才安装；失败立即停止，保留命令/stdout/stderr/退出码/树级清理回执，不把缺件错误改成跳过。
隔离验证须实际进行 CLI 状态/已授权非敏感格式最小用例/错误退出码/输出重新打开；本轮只形成计划，不调用 Connector init/auth/status。

## WorkBuddy 与最小后续整改（另授权）

仅在真实托管解释器与普通 Skill Bash 绑定分别观测后才判定运行目标。Connector 仍 pin solar 0.3.1；未来只在确认公开不可变 source+hash约束路径、部署安装与回滚后，最小修改 cli.json 安装声明至获准0.3.2并同步关联metadata/文档。
不修改 Skill、不假设 file:/// 是可公开来源、不把手动sidecar校验冒充安装器 hash enforcement。
先 Connector 后独立 Skill 的安装/卸载/实际用例验证均需新授权与正式入口权利；若无私测入口则阻断，不造 preview 或要求聊天交凭据。
本轮不得模型/CH08/Word/PDF/发布/Phase E-F-G。

机器计划：''' + ref(C / 'download-plan.json') + '\n')
    docrows = [(d['path'],d['bytes'],d['sha256'],d['member_count'],'无 LICENSE' if not d['licenses'] else '含 licenses/LICENSE') for d in load(license_dir / 'document-identity.json')['documents']]
    put(D / 'DOCUMENT_CLI_ARTIFACT_IDENTITY.md', '''# document-cli 1.2.0 双构件身份裁定

**DOCUMENT_CLI_ARTIFACT_IDENTITY=BLOCKED**。同名同版本不等于同构件；不得按 mtime/是否含LICENSE/新 generator 自动选。

''' + table(['原路径','B','SHA256','members','LICENSE'], docrows) + '''
两个 ZIP 安全唯一、CRC/RECORD 静态校验已有真实原证；13模块原字节相同，且当前源码/Git LF一致，但共同 METADATA/WHEEL/RECORD 不同，dist 多 licenses/LICENSE。
候选曾有 No module named pip 的失败，后用 setuptools backend 的成功 JSON；原 build-source copy 现不可得，source commit/environment 绑定不足。dist sidecar 是身份凭据，不是构建来源证明。
当前模块相同不能倒推构建时commit。完整 member SHA、generator、依赖声明、METADATA/license原件与历史streams见 document-identity.json / document-originals。

后续需要两构件各自的原构建输入、精确commit、解释器/工具链、完整命令streams和许可来源链、不可变可获取渠道。若无法补足，另申请新无冲突版本可追溯隔离构建；本轮不重打1.2.0，不择一、不发布。

''' + ref(license_dir / 'document-identity.json') + '\n')
    put(D / 'QUALITY_REPORT.md', '''# 独立 QA 入口与当前状态

**INDEPENDENT_QA=NOT_RUN / PENDING_INDEPENDENT_QA**。作者仅执行候选生成、冻结输入重建比较、AST/文档/卫生/范围自检；没有签署独立 QA。
这是有实际输入、范围与待验项的审核索引，不是模拟 QA 结果。真正审查完成后，唯一writer须原字节复制审查员结论并明确其冻结快照范围，再做新payload限定复审。

## 输入与冻结边界

- RUN/developer-freeze-index.json：源码/新文档/脚本/允许证据逐路径size/SHA、来源映射、脱敏身份；独立 QA 必须先核此索引 SHA及每件实际字节。
- RUN/frozen-inputs.json：本地原元数据胶囊，177件，SHA `171656d7edd77345ba25edc333c2450db000dbbc38fdd30242531ecbad19f5e9`。仅本地，含公开联系字段，不可直接共享。
- 重新读取 source-research/official-metadata/raw 和 pep658/raw 与响应索引、全部旧12图/绑定、license-identity 原来源文本、document 原件；不能只复述 RESULT。
- 共享 raw不入payload：source-research/sharing-index.final.json 是185件脱敏/最小派生allowlist；原/派生SHA分别记录，PEP658索引期望摘要未核。

## 独立复核必测

1. 从十二旧图分别抽42名称/43精确版本，校核官方对应与tzdata差异。
2. 由真实Requires-Dist重新求marker/extras固定点，保留magika澄清；核全部传递依赖及Python范围。
3. 逐115文件核官方 URL/SHA/文件名/name/version/tag/ABI/platform/OS最低条件；拒绝yanked/t-GIL/musl混入。
4. 区分官方记录摘要与实际本地wheel摘要（后者0），核所有license/source/READY/closure状态不升级。
5. 复核三项精确文本缺口、全部42再分发BLOCKED、双document identity与外置12/optional11/历史重放限制。
6. 负向真实变异：同名不同version、同version不同SHA、错误Python/ABI/platform、Requires-Python、删传递node或边、错marker/extras、未取得却claimed hash pass、unknown license却PASS、unknown officialsource却READY、缺件却closurePASS；独立保存变异输入、运行回执与拒绝诊断，不能预填expected结果。
7. 核无下载/安装/生产改动/Skill变更；核task允许树隐私/秘密与提交blob字节；审新payload exact成员集。

脚本命令：以现有绝对 .venv/Scripts/python.exe -I -B 调用 scripts/locktool.py validate --inputs <frozen-inputs> --candidate <完整候选>；须经 RUN/record_command.py 以 quality 独名保存 exact inputs/stdout/stderr/退出码。单条<=120秒，质量角色预算200秒，任务总1200秒含失败。

开发者自检日志：RUN/commands/developer-*；最终已完成时间/失败/保护读回另存 developer-final-state.json。作者自检不计独立检查数量。
没有新源码审阅ZIP；独立QA完成且payload限定复审通过前不封包。
''')
    put(D / 'NEXT_GATE.md', '''# 下一门禁与停止位置

当前停在不可安装来源候选，等待真正独立 QA；不封 ZIP，不下载/安装，不修改 Connector/Skill，不模型/CH08/报告生成，不push/merge/reset/rebase/发布/Phase E/F/G。

| 门禁 | 当前状态 | 下一条件 |
|---|---|---|
| SOURCE_RESEARCH | COMPLETE（不含构件取得） | 独立核官方原元数据与全12图 |
| INDEPENDENT_QA | NOT_RUN / PENDING | 冻结index后独立实测负向与原证复核 |
| ARTIFACT_ACQUISITION | NOT_AUTHORIZED | 精确URL/hash/target/notice条件独立授权 |
| LICENSE_REVIEW/REDISTRIBUTION | BLOCKED（42名称） | 三项文本关联、全部actual wheel NOTICE/native与法律核查 |
| DOCUMENT_CLI_ARTIFACT_IDENTITY | BLOCKED | 双构件来源commit/build/许可链或新无冲突版本审批 |
| DEPENDENCY_CLOSURE | BLOCKED | yanked缺口/平台缺口+完整可信实际构件/许可/资源 |
| FORMAL_FIRST_TARGET | UNCONFIRMED | 直接观测Skill/Connector解释器/patch/ABI/OS而非DEV代替 |
| EXTERNAL_BASELINE_RESOURCES | NOT_SELF_CONTAINED | 十二件受控来源、引擎/lock/逐件hash绑定及分发权 |
| OPTIONAL_DEMO_FIXTURES | NOT_BUNDLED | 可选独立审批；不得作真实输入 |
| HISTORICAL_RECEIPTS | PARTIALLY_NOT_REPLAYABLE | 保持原件缺失限制，不伪造 |

## 继承的八项旧门禁

TRUSTED_WHEEL_SOURCE=PASS_LOCAL_SOURCE_ONLY；WHEEL_BUILD=WHEEL_BUILT_LOCAL；WHEEL_CONTENT=PASS_LIMITED；DEPENDENCY_CLOSURE=BLOCKED；ISOLATED_INSTALLATION=NOT_TESTED；WORKBUDDY_SKILL_RUNTIME=NOT_TESTED；WORKBUDDY_HOST_E2E=BLOCKED；PROFESSIONAL_SEMANTIC_REVIEW=NOT_TESTED。

历史客户端/Skill导入PASS仅原作用域；roof CH08=BLOCKED_NO_DRAFT，ground=NOT_TESTED_BLOCKED_BY_STOP_GATE；roof/ground schema/strict=NOT_TESTED_NO_DRAFT；PHASE_D_CONTENT_REVIEW=USER_REVIEW_REQUIRED。
Phase C 六类财务方法/候选/独立付款等未决风险保留，不以账面残值替代处置现金、不以应付当已付、不以项目IRR代股东回收。
Phase D 仍为两案 CH05/08/10/14/15/16/17/18。PDF公式复制检索、四文件同源、专业签审、全仓回归、正式发布及E/F/G仍各自阻断。

独立 QA 后可由唯一writer原字节纳入审查结论并正常新commit，冻结新payload并请限定复审；最终分享包必须另核成员唯一/路径安全/CRC/size/SHA/全集/脱敏才可封，不得把当前候选commit叫发布。
''')
    artifacts = [ident(p) for p in sorted(C.iterdir()) if p.is_file()]
    put(C / 'artifact-index.json', {'schema': 'generated-candidate-artifacts/1', 'files': artifacts, 'source_head': lock.BASE})
    print(json.dumps({'formal_files': [p.name for p in sorted(D.iterdir()) if p.is_file()], 'candidate_files': artifacts}, ensure_ascii=True))


if __name__ == '__main__':
    main()
