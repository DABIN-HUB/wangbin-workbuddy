"""Freeze prior independent 41-case expectations plus new QA-only variants for 0.2.7.
This generator NEVER edits production or prior QA evidence.
"""
from pathlib import Path
root = Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/docs/products/wangbin-tender-analyzer')
src = (root / 'qa-audit-r1-new-026-probe.py').read_text(encoding='utf-8')
src = src.replace('q06_independent_026_rerun1', 'q06_independent_027_rerun1')
src = src.replace('0.2.6-skill-candidate', '0.2.7-skill-candidate')
src = src.replace('1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a', '12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09')
src = src.replace("manifest['version']=='0.2.6'", "manifest['version']=='0.2.7'")
src = src.replace('c687c1f81e348fd573997a96719726f362e76dffe71cb62818ec54b11460c4db', '100de72a1562162446d925c25f5d499d723f9f0ab60b95bcbccd745b3eb52cc6')
extra = '''# Newly predeclared independent equivalence, tense, object, evidence, and date controls.
add('Q01-unable-present','1. 必须支持自动备份。','1. 自动备份这一功能目前无法实现。',expected=('已定位','可能不充分','不适用','不适用'))
add('Q02-not-available-yet','1. 必须支持自动备份。','1. 自动备份还未投入使用。',expected=('已定位','可能不充分','不适用','不适用'))
add('Q03-proposed-future','1. 必须支持自动备份。','1. 自动备份已纳入后续研发计划，现阶段无法提供。',expected=('已定位','可能不充分','不适用','不适用'))
add('Q04-positive-operational','1. 必须支持自动备份。','1. 自动备份已经部署启用，并可执行每日备份。',expected=('已定位','已覆盖（文本层面）','不适用','不适用'))
add('Q05-no-cross-subject','1. 必须支持自动备份。\\n2. 必须支持离线查询。','1. 目前尚无法提供自动备份。\\n2. 离线查询现已投入使用。',expected=[('已定位','可能不充分','不适用','不适用'),('已定位','已覆盖（文本层面）','不适用','不适用')])
add('Q06-evidence-not-issued','1. 必须提供营业执照。','1. 营业执照已递交。',{'营业执照.txt':'营业执照尚未颁发；此为申请材料，不是营业执照。'},expected=('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('Q07-evidence-empty-wrapper','1. 须提供certificate.txt资质证明。','1. 附件certificate.txt为资质证明。',{'certificate.txt':'certificate.txt：此文件仅作为示意，不包含任何证照正文。'},expected=('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('Q08-evidence-genuine-text','1. 必须提供营业执照。','1. 营业执照已递交。',{'营业执照.txt':'营业执照文本：统一社会信用代码为虚构示例编号。'},expected=('已定位','已覆盖（文本层面）','已提供（可读文本）','支持（文本层面）'))
add('Q09-cross-object','1. 必须提供甲类资质证明。\\n2. 必须提供乙类资质证明。','1. 甲类证明已提交。\\n2. 乙类证明已提交。',{'甲类.txt':'甲类证明文本：甲类有效。'},expected=[('已定位','已覆盖（文本层面）','已提供（可读文本）','支持（文本层面）'),('已定位','可能不充分','未提供（限已提供材料）','未核验')])
add('Q10-cross-object-negative','1. 必须提供甲类资质证明。\\n2. 必须提供乙类资质证明。','1. 甲类证明已提交。\\n2. 乙类证明已提交。',{'乙类.txt':'乙类证明尚在申请；本文件不是乙类证明。'},expected=[('已定位','可能不充分','未提供（限已提供材料）','未核验'),('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）')])
add('Q11-date-shift','1. 丁类资质须有效覆盖2046-04-11至2047-04-10，附丁类证明 certificate.txt。','1. 丁类有效期覆盖该期，见certificate.txt。',{'certificate.txt':'丁类证明：2046-04-11生效，有效截止2047-04-09。'},[['certificate.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('Q12-date-boundary','1. 丁类资质须有效覆盖2046-04-11至2047-04-10，附丁类证明 certificate.txt。','1. 丁类有效期覆盖该期，见certificate.txt。',{'certificate.txt':'丁类证明：2046-04-11生效，有效截止2047-04-10。'},[['certificate.txt','1']],('已定位','已覆盖（文本层面）','已提供（可读文本）','支持（文本层面）'))
'''
assert src.count('records=[]\nfor case in cases:') == 1
src = src.replace('records=[]\nfor case in cases:', extra + 'records=[]\nfor case in cases:')
src = src.replace("'N04-rephrase-scope','N05-no-catalog-negative','R18-no-catalog'", "'N04-rephrase-scope','N05-no-catalog-negative','R18-no-catalog','Q01-unable-present','Q02-not-available-yet','Q03-proposed-future','Q05-no-cross-subject','Q06-evidence-not-issued','Q07-evidence-empty-wrapper','Q10-cross-object-negative'")
src = src.replace("records=[]\nfor case in cases:", "assert len(cases)==53 and len({c['id'] for c in cases})==53\nrecords=[]\nfor case in cases:")
path = root / 'qa-audit-r1-new-027-probe.py'
assert not path.exists()
path.write_text(src, encoding='utf-8')
print(path)
