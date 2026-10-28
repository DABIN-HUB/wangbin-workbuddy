"""SYNTHETIC malformed packets and context changes do not corrupt sessions."""
from copy import deepcopy
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.intake import IntakeSession

CAT=Catalog()

@pytest.mark.parametrize('update',[
 {'field_id':[],'value':1}, {'field_id':'site.total_area','value':1,'unit':[]},
 {'field_id':'project.name','value':'SYNTHETIC','unit':{}},
 {'field_id':'site.total_area','value':1,'unit':'m2','source_kind':{}},
 {'field_id':'site.total_area','value':'1000','unit':'m2'},
 {'field_id':'project.name','value':'SYNTHETIC','value_from_model':'invented'},
])
def test_bad_packet_has_contract_error_and_no_partial_writes(update):
 s=IntakeSession.new('SYNTHETIC-BOUNDS','industrial_rooftop',CAT);before=s.project.to_dict()
 with pytest.raises(ContractError):s.submit('bad',[update],expected_revision=0)
 assert s.project.to_dict()==before

def test_target_change_keeps_other_fact_values_and_evidence():
 s=IntakeSession.new('SYNTHETIC-TARGET','industrial_rooftop',CAT)
 s.submit('a',[{'field_id':'system.dc_capacity','value':2,'unit':'MWp'}],expected_revision=0)
 before=deepcopy(s.project.values['system.dc_capacity'])
 s.submit('b',[{'field_id':'targets.payback_years','value':1,'unit':'year'}],expected_revision=1)
 assert s.project.values['system.dc_capacity']==before
 assert 'capex.items' not in s.project.values and not s.status()['maturity']['can_execute_calculation']

def test_location_change_demotes_verified_site_dependent_data_without_replacing_values():
 s=IntakeSession.new('SYNTHETIC-SITE','industrial_rooftop',CAT)
 s.submit('a',[{'field_id':'grid.connection_point','value':'SYNTHETIC-POINT'}],expected_revision=0)
 s.review('b','grid.connection_point',expected_revision=1,reviewer='SYNTHETIC',reason='SYNTHETIC evidence',license_status='AUTHORIZED')
 out=s.submit('c',[{'field_id':'site.address','value':'SYNTHETIC different site'}],expected_revision=2)
 assert 'grid.connection_point' in out['invalidated_field_ids']
 r=s.project.values['grid.connection_point'];assert r['value']=='SYNTHETIC-POINT' and r['status']=='UNVERIFIED'

def test_assumption_cannot_be_verified_by_review_action():
 s=IntakeSession.new('SYNTHETIC-ASSUMPTION','industrial_rooftop',CAT)
 # Envelope kept as an explicit assumed fixture; review must not upgrade it.
 from wangbin_solar_pv.provenance import make_record
 s.project.values['site.total_area']=make_record(CAT,'site.total_area',100,source_kind='ASSUMPTION')
 with pytest.raises(ContractError):s.review('b','site.total_area',expected_revision=0,reviewer='SYNTHETIC',reason='SYNTHETIC',license_status='AUTHORIZED')
 assert s.project.values['site.total_area']['status']=='ASSUMED'
