"""SYNTHETIC parser-intake boundary, including full attachment hash retention."""
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.parsers import parse_attachment
from wangbin_solar_pv.errors import ContractError

CAT=Catalog()

def test_parsed_candidate_acceptance_keeps_sha_and_is_not_verification(tmp_path):
 path=tmp_path/'SYNTHETIC.txt';path.write_text('project.name: SYNTHETIC\nsite.total_area: 1000 m2\n',encoding='utf8')
 parsed=parse_attachment(path,tmp_path,catalog=CAT,work_root=tmp_path/'work')
 s=IntakeSession.new('SYNTHETIC-PARSER-INTAKE','industrial_rooftop',CAT)
 s.accept_candidates('attachment1',parsed,[0,1],expected_revision=0)
 assert s.project.values['site.total_area']['value']==1000
 assert s.project.values['site.total_area']['status']=='UNVERIFIED'
 assert s.export()['source_snapshot']['attachments'][0]['sha256']==parsed['sha256']
 assert s.export()['source_snapshot']['attachments'][0]['source_name']==path.name
 assert len(s.status()['maturity']['next_questions'])<=5

def test_explicit_document_currency_scales_quote_without_inventing_tax_year(tmp_path):
 path=tmp_path/'SYNTHETIC.txt';path.write_text('project.currency: CNY\ncapex.user_budget: 100 万元\n',encoding='utf8')
 result=parse_attachment(path,tmp_path,catalog=CAT,work_root=tmp_path/'work')
 assert result['status']=='PARSED',result
 rec=next(r for r in result['candidates'] if r['field_id']=='capex.user_budget')
 assert rec['value']==1000000 and rec['economic_basis'] is None
 assert rec['normalization']['currency']=='CNY'

def test_explicit_source_row_identifier_is_not_repaired_or_replaced(tmp_path):
 path=tmp_path/'SYNTHETIC.csv'
 path.write_text('load.series.row_id,load.series.energy (kWh)\nROW-A,10\ninvalid row,20\n',encoding='utf8')
 result=parse_attachment(path,tmp_path,catalog=CAT,work_root=tmp_path/'work')
 assert result['status']=='PARTIAL'
 rows=result['candidates'][0]['value']
 assert [r['row_id'] for r in rows]==['ROW-A','invalid row']
 assert rows[0]['fields']['load.series.row_id']['original_value']=='ROW-A'
 assert rows[1]['fields']['load.series.row_id']['original_value']=='invalid row'
