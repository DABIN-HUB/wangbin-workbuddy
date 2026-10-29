"""SYNTHETIC regression: historical evidence cannot revive a stale approval."""
from copy import deepcopy
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import resolve_conflict,register_candidate
CAT=Catalog()


def stale_candidate():
    s=IntakeSession.new('SYNTHETIC-CONTEXT','industrial_rooftop',CAT)
    s.submit('initial',[{'field_id':'site.address','value':'SYNTHETIC-SITE-A'},
                       {'field_id':'grid.connection_point','value':'SYNTHETIC-GRID-A'}],expected_revision=0)
    reviewed=s.review('review-a','grid.connection_point',expected_revision=1,reviewer='SYNTHETIC-REVIEWER-A',reason='SYNTHETIC evidence for site A',license_status='AUTHORIZED')
    cid=reviewed['accepted_candidate_ids'][0]
    s.revise('move',[{'field_id':'site.address','value':'SYNTHETIC-SITE-B'}],reason='SYNTHETIC switch site',expected_revision=2)
    return s,cid


@pytest.mark.parametrize('api',['intake','provenance','registration','legacy_history'])
def test_context_invalidated_verified_candidate_never_revives_without_new_review(api):
    s,cid=stale_candidate();historical=deepcopy(s.project.candidates[cid])
    assert historical['status']=='VERIFIED'
    if api=='legacy_history':
        # Compatibility with already persisted Phase2D invalidation events.
        for event in s.project.history:
            if event.get('event')=='context_invalidated':event.pop('candidate_ids',None)
    if api=='registration':
        register_candidate(s.project,historical,CAT,replacement_reason='SYNTHETIC source replay, not verification')
    else:
        s.submit('different-grid',[{'field_id':'grid.connection_point','value':'SYNTHETIC-GRID-B'}],expected_revision=3)
        if api in {'intake','legacy_history'}:
            s.resolve('choose-old','grid.connection_point',cid,expected_revision=4,reviewer='SYNTHETIC-CHOOSER',reason='SYNTHETIC choose old source only')
        else:
            resolve_conflict(s.project,'grid.connection_point',cid,reviewer='SYNTHETIC-CHOOSER',reason='SYNTHETIC choose only')
    active=s.project.values['grid.connection_point']
    assert active['value']=='SYNTHETIC-GRID-A'
    assert active['status']=='UNVERIFIED' and active['reviewer'] is None
    assert s.project.candidates[cid]==historical
    assert s.export()['source_snapshot']['context_invalidations']


def test_separate_review_after_context_change_can_establish_new_approval():
    s,cid=stale_candidate()
    reviewed=s.review('review-b','grid.connection_point',expected_revision=3,reviewer='SYNTHETIC-REVIEWER-B',reason='SYNTHETIC new evidence for site B',license_status='AUTHORIZED')
    new_id=reviewed['accepted_candidate_ids'][0];assert new_id!=cid
    s.submit('different',[{'field_id':'grid.connection_point','value':'SYNTHETIC-OTHER'}],expected_revision=4)
    s.resolve('choose-new','grid.connection_point',new_id,expected_revision=5,reviewer='SYNTHETIC-CHOOSER',reason='SYNTHETIC select newly reviewed source')
    assert s.project.values['grid.connection_point']['status']=='VERIFIED'
    assert s.project.values['grid.connection_point']['reviewer']=='SYNTHETIC-REVIEWER-B'


def test_nested_verified_atoms_are_demoted_when_old_container_is_reactivated():
    s=IntakeSession.new('SYNTHETIC-NESTED-CONTEXT','industrial_rooftop',CAT)
    def monthly(poa):return [{'field_id':'resource.monthly','value':[{'row_id':'r1','fields':{'resource.monthly.month':{'value':1},'resource.monthly.poa':{'value':poa,'unit':'kWh/m2'}}}]}]
    s.submit('first',monthly(100),expected_revision=0)
    out=s.review('review','resource.monthly',expected_revision=1,reviewer='SYNTHETIC-A',reason='SYNTHETIC old site',license_status='AUTHORIZED');cid=out['accepted_candidate_ids'][0]
    s.submit('move',[{'field_id':'site.address','value':'SYNTHETIC new site'}],expected_revision=2)
    s.submit('other',monthly(200),expected_revision=3)
    s.resolve('choose','resource.monthly',cid,expected_revision=4,reviewer='SYNTHETIC',reason='SYNTHETIC select only')
    active=s.project.values['resource.monthly'];assert active['status']=='UNVERIFIED'
    assert all(r['status']=='UNVERIFIED' and r['reviewer'] is None for r in active['value'][0]['fields'].values())
    assert s.project.candidates[cid]['status']=='VERIFIED'


def test_month_ordinal_has_no_physical_unit_to_guess_and_rejects_fake_units():
    s=IntakeSession.new('SYNTHETIC-ORDINAL','industrial_rooftop',CAT)
    from wangbin_solar_pv.errors import ContractError
    with pytest.raises(ContractError,match='UNIT_MISMATCH'):
        s.submit('bad',[{'field_id':'resource.monthly','value':[{'row_id':'r1','fields':{'resource.monthly.month':{'value':1,'unit':'m2'}}}]}],expected_revision=0)
    assert s.project.revision==0
