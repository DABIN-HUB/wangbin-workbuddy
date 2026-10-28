"""Explicit SYNTHETIC test records, never a real site or real external source."""
from wangbin_solar_pv.provenance import make_record


def record(catalog, fid, value, *, instance_id=None, status="UNVERIFIED", **kwargs):
    options = dict(source_kind="USER_PROVIDED", source_id="SYNTHETIC-LOCAL",
        source_url_or_attachment="SYNTHETIC:authorized-test", source_section_or_cell="SYNTHETIC explicitly authored test record",
        confidence_basis="SYNTHETIC fictional data and review; NOT a real project", license_status="AUTHORIZED",
        status=status, reviewer="SYNTHETIC-REVIEWER" if status == "VERIFIED" else None,
        location_status="TEXT_FRAGMENT", field_instance_id=instance_id)
    options.update(kwargs)
    return make_record(catalog, fid, value, **options)


def row(catalog, group, rid, values, *, status="UNVERIFIED"):
    fields = {group+"."+name: record(catalog,group+"."+name,value,instance_id=group+":"+rid+":"+name,status=status)
              for name,value in values.items()}
    if group+".row_id" in catalog.fields:
        fields[group+".row_id"] = record(catalog,group+".row_id",rid,instance_id=group+":"+rid+":row_id",status=status)
    return {"row_id":rid,"fields":fields}


def put_rows(project,catalog,group,rows, *, status="UNVERIFIED"):
    project.values[group] = record(catalog,group,rows,status=status)


def scalar_item(catalog,fid,value,instance_id):
    return record(catalog,fid,value,instance_id=instance_id)
