"""Engineering/observation input audits; no yield, revenue or investment calculation."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
import math

from .conditions import known, condition_state
from .errors import Issue
from .units import validate_timezone
from .validation import row_value


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float, Decimal)) and (value.is_finite() if isinstance(value, Decimal) else math.isfinite(value))


def _rows(project, fid):
    value = known(project, fid)
    return value if isinstance(value, list) else []


def _orientation(a, b, c):
    value = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return 0 if value == 0 else (1 if value > 0 else -1)


def _on_segment(a, b, c):
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def _intersects(a, b, c, d):
    o1, o2, o3, o4 = _orientation(a,b,c), _orientation(a,b,d), _orientation(c,d,a), _orientation(c,d,b)
    return (o1*o2 < 0 and o3*o4 < 0) or any((o == 0 and _on_segment(x,y,z)) for o,x,y,z in ((o1,a,b,c),(o2,a,b,d),(o3,c,d,a),(o4,c,d,b)))


def assess_input_quality(project, catalog):
    issues=[]
    def issue(code,fid,message,severity="ERROR"):
        issues.append(Issue(code,fid,message,severity))
    pf = known(project,"grid.power_factor")
    if _number(pf) and pf <= 0:
        issue("POWER_FACTOR_NOT_POSITIVE","grid.power_factor","冻结文字要求功率因数严格正；保留原值但禁止用于换算/高等级")
    ac, apparent = known(project,"system.ac_capacity"), known(project,"grid.transformer_capacity")
    if all(_number(v) for v in (ac,apparent,pf)) and pf > 0 and Fraction(str(ac)) > Fraction(str(apparent))*Fraction(str(pf)):
        issue("TRANSFORMER_LIMIT_EXCEEDED","system.ac_capacity","已声明交流容量超过视在容量与明确功率因数给出的边界")
    permitted = known(project,"grid.available_capacity")
    if _number(ac) and _number(permitted) and ac > permitted:
        issue("GRID_CAPACITY_EXCEEDED","system.ac_capacity","已声明交流容量超过可接入容量，需确认方案")
    dc, count, wp = [known(project,"system."+name) for name in ("dc_capacity","module_count","module_power")]
    if all(_number(v) for v in (dc,count,wp)) and Fraction(str(dc))*1000 != Fraction(str(count))*Fraction(str(wp)):
        issue("DECLARED_DC_CAPACITY_MISMATCH","system.dc_capacity","给定直流容量与组件清单不一致，不自动改装机")
    ratio = known(project,"system.dc_ac_ratio")
    if all(_number(v) for v in (dc,ac,ratio)) and ac > 0 and Fraction(str(dc)) != Fraction(str(ac))*Fraction(str(ratio)):
        issue("DECLARED_DC_AC_RATIO_MISMATCH","system.dc_ac_ratio","给定容配比与已声明容量不一致")
    evaluation = known(project,"project.evaluation_date")
    expiry = known(project,"grid.opinion_valid_until")
    if isinstance(evaluation,str) and isinstance(expiry,str) and expiry < evaluation:
        issue("GRID_OPINION_EXPIRED","grid.opinion_valid_until","接入意见已过评价基准日，不沿用confirmed")
    if known(project,"grid.opinion_status") == "rejected":
        issue("GRID_REJECTED","grid.opinion_status","已知接入拒绝不能被财务目标抵消")
    if known(project,"site.rights_status") in {"disputed","prohibited"}:
        issue("SITE_RIGHTS_BLOCKED","site.rights_status","权属争议或禁止建设须独立处理")
    allowed, added = known(project,"roof.allowable_additional_load"), known(project,"roof.design_added_load")
    if _number(allowed) and _number(added) and added > allowed:
        issue("ROOF_LOAD_EXCEEDS_ALLOWABLE","roof.design_added_load","给定新增荷载超过允许附加荷载，不冒充结构鉴定")
    for row in _rows(project,"risk.items"):
        severity,state = row_value(row,"risk.items.severity"),row_value(row,"risk.items.evidence_state")
        if severity == "veto" and state == "confirmed":
            issue("CONFIRMED_VETO","risk.items","已证实否决风险独立阻断")
        elif severity in {"veto","major"} and state in {"pending","conflicted"}:
            issue("MAJOR_RISK_PENDING","risk.items","重大未决/冲突不得由收益掩盖")
    for fid in ("site.timezone","load.timezone"):
        zone = known(project,fid)
        if zone is not None:
            try:
                validate_timezone(zone)
            except ValueError:
                issue("INVALID_IANA_TIMEZONE",fid,"需真实IANA时区，不能猜测位置或偏移")
    issues.extend(_geometry(project))
    load_needed = condition_state("IN-C04",project,catalog)["truth"] == "T"
    for group in ("resource.timeseries","load.series","tariff.market_series","storage.dispatch"):
        rows = _rows(project,group)
        if not rows or (group=="load.series" and not load_needed):
            continue
        period = project.values[group].get("measurement_period")
        if not isinstance(period,dict) or not all(period.get(k) for k in ("start","end","timezone")):
            issue("OBSERVATION_PERIOD_NOT_DECLARED",group,"时序需明确覆盖区间/时区，不按行数猜全年","WARNING")
            continue
        try:
            validate_timezone(period["timezone"])
            start,end = [datetime.fromisoformat(period[k].replace("Z","+00:00")) for k in ("start","end")]
            if start.utcoffset() is None or end.utcoffset() is None or end <= start:
                raise ValueError
            points=[]
            last_minutes=None
            for row in rows:
                stamp = row_value(row,group+".timestamp")
                if not isinstance(stamp,str):
                    raise ValueError
                point = datetime.fromisoformat(stamp.replace("Z","+00:00"))
                if point.utcoffset() is None:
                    raise ValueError
                points.append(point.astimezone(timezone.utc))
                last_minutes = row_value(row,group+".interval_minutes")
            if not _number(last_minutes):
                raise ValueError
            finish = points[-1] + timedelta(minutes=float(last_minutes))
            if points[0] != start.astimezone(timezone.utc) or finish != end.astimezone(timezone.utc):
                issue("OBSERVATION_BOUNDARY_GAP",group,"实际首尾观测与声明覆盖区间不一致，不补零","WARNING")
            if group == "load.series" and (end-start).total_seconds() < 365*24*60*60:
                issue("LOAD_REPRESENTATIVENESS_REVIEW_REQUIRED",group,"不足完整年度的负荷需独立代表性映射审查，当前未实现该映射","WARNING")
        except (ValueError,TypeError,OverflowError):
            issue("OBSERVATION_PERIOD_INVALID",group,"观测区间或时间轴不能可靠核验","WARNING")
    for row in _rows(project,"load.monthly_bills"):
        start,end = row_value(row,"load.monthly_bills.period_start"),row_value(row,"load.monthly_bills.period_end")
        if start and end and start > end:
            issue("BILL_PERIOD_ORDER","load.monthly_bills","账期起止倒置")
    if load_needed and _rows(project,"load.monthly_bills") and len(_rows(project,"load.monthly_bills")) < 12:
        issue("BILLS_TWELVE_MONTHS_REQUIRED","load.monthly_bills","近12个月账单未齐，不能以账单总量替代负荷曲线","WARNING")
    options = _rows(project,"scenarios.options")
    if options:
        kinds={row_value(row,"scenarios.options.kind") for row in options}
        if not {"baseline","alternative"} <= kinds:
            issue("ALTERNATIVE_PLAN_MISSING","scenarios.options","预可研需基准与可行替代方案，尚未完成方案计算","WARNING")
    return issues


def _geometry(project):
    rows=_rows(project,"site.boundary_vertices")
    if not rows:
        return []
    issues=[]
    def issue(code,message,severity="ERROR"):
        issues.append(Issue(code,"site.boundary_vertices",message,severity))
    if known(project,"site.crs") is None:
        issue("POLYGON_CRS_REQUIRED","顶点必须声明坐标系，不能补造WGS84")
    if len(rows) > 512:
        issue("GEOMETRY_MANUAL_REVIEW_REQUIRED","超过512顶点的复杂几何保留全部数据并要求专项几何复核；不截断或伪称已校核","WARNING")
        return issues
    rings=defaultdict(list)
    for row in rows:
        values=[row_value(row,"site.boundary_vertices."+name) for name in ("polygon_id","ring_index","vertex_index","longitude","latitude")]
        polygon,ring,index,x,y=values
        if not isinstance(polygon,str) or not isinstance(ring,int) or not isinstance(index,int) or not _number(x) or not _number(y):
            issue("POLYGON_VERTEX_INCOMPLETE","顶点索引/坐标缺失，不能推算边界")
            continue
        rings[(polygon,ring)].append((index,(Fraction(str(x)),Fraction(str(y)))))
    for entries in rings.values():
        if len({i for i,_ in entries}) != len(entries):
            issue("POLYGON_VERTEX_INDEX_DUPLICATE","环内顶点序号不能重复")
            continue
        entries.sort(key=lambda item:item[0])
        points=[p for _,p in entries]
        if len(points) < 4 or points[0] != points[-1]:
            issue("POLYGON_NOT_CLOSED","环必须真实闭合且至少含三个不同顶点，不自动补点")
            continue
        if len(set(points[:-1])) < 3 or len(set(points[:-1])) != len(points)-1:
            issue("POLYGON_DEGENERATE","重复或不足的独立顶点不能构成有效边界")
            continue
        edges=list(zip(points,points[1:]))
        found=False
        for i,(a,b) in enumerate(edges):
            for j in range(i+2,len(edges)):
                if i==0 and j==len(edges)-1:
                    continue
                if _intersects(a,b,*edges[j]):
                    found=True
                    break
            if found:
                break
        if found:
            issue("POLYGON_SELF_INTERSECTION","边界自交须重测/修正，不以面积估算掩盖")
    if len(rings) > 1:
        issue("GEOMETRY_TOPOLOGY_REVIEW_REQUIRED","多面/洞的跨环拓扑须专项复核；单环检查不冒充完整GIS有效性","WARNING")
    return issues
