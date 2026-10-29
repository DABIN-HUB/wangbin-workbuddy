"""Project engineering adapter. No area-density or DC allocation defaults."""
from __future__ import annotations

from decimal import Decimal

from ..errors import ContractError
from .common import integer, precision_context
from .engineering import evaluate


def capacity(inputs):
    """Consume checked raw equipment facts, retaining DC/AC nameplate labels."""
    digits = inputs.methods.require("precision.digits")
    with precision_context(digits):
        count = integer(inputs.value("system.module_count"), minimum=1)
        inv_count = integer(inputs.value("system.inverter_count"), minimum=1, maximum=101)
        wp = inputs.numeric("system.module_power")
        dc = evaluate("F-DC-CAPACITY", {"equipment.module_count": count,
            "equipment.module_power_kwp": wp / 1000}, {"precision_digits": digits})["value"]
        unit_ac = inputs.numeric("system.inverter_unit_ac")
        ids = [f"inv-{i+1}" for i in range(inv_count)]
        ac = evaluate("F-AC-CAPACITY", {"equipment.inverters.ids": ids,
            "equipment.inverters.rated_ac_kw": dict.fromkeys(ids, unit_ac)},
            {"precision_digits": digits})["value"]
        allocations = inputs.methods.require("energy.dc_allocation")
        if len(allocations) != inv_count or sum(allocations, Decimal(0)) != 1:
            raise ContractError("ENERGY_DC_ALLOCATION")
        efficiency = inputs.numeric("system.inverter_efficiency")
        for fid, actual in (("system.dc_capacity", dc), ("system.ac_capacity", ac),
                            ("system.dc_ac_ratio", dc/ac)):
            if fid in inputs.values:
                declared = inputs.numeric(fid)
                tolerance = inputs.methods.require("precision.abs_tolerance")
                relative = inputs.methods.require("precision.rel_tolerance")
                if abs(declared-actual) > max(tolerance, abs(actual)*relative):
                    raise ContractError("ENERGY_CAPACITY_INCONSISTENT", fid)
        total = inputs.numeric("site.total_area")
        excluded = inputs.numeric("site.exclusion_area")
        usable = evaluate("F-USABLE-AREA", {"site.total_area": total,
            "site.exclusion_area": {"validated-union": excluded}},
            {"precision_digits": digits, "index_ids": {"site.exclusion_area": ["validated-union"]}})["value"]
        declared_usable = inputs.numeric("site.usable_area")
        if declared_usable > usable:
            raise ContractError("ENERGY_AREA_INCONSISTENT")
        # GCR is explicitly supplied, not a universal W/m² heuristic. This is
        # the declared module surface-area / occupied-area layout convention.
        module_area = inputs.numeric("system.module_length") * inputs.numeric("system.module_width")
        gcr = inputs.numeric("layout.ground_coverage_ratio")
        if gcr <= 0 or count * module_area / gcr > declared_usable:
            raise ContractError("ENERGY_LAYOUT_AREA")
        inputs.value("site.area_basis")
        inputs.numeric("layout.tilt")
        inputs.numeric("layout.azimuth")
        inputs.value("system.mounting_type")
        if inputs.numeric("layout.row_pitch") < inputs.numeric("system.module_width"):
            raise ContractError("ENERGY_LAYOUT_PITCH")
        strings = integer(inputs.value("system.parallel_strings"), minimum=1)
        per_string = integer(inputs.value("system.modules_per_string"), minimum=1)
        if strings * per_string != count:
            raise ContractError("ENERGY_STRING_COUNT")
        allocated_strings = [fraction*strings for fraction in allocations]
        if any(value != value.to_integral_value() for value in allocated_strings):
            raise ContractError("ENERGY_STRING_ALLOCATION")
        voc = inputs.numeric("system.module_voc") * per_string
        vmp = inputs.numeric("system.module_vmp") * per_string
        if (voc > inputs.numeric("system.inverter_max_dc_voltage")
                or not inputs.numeric("system.inverter_mppt_min") <= vmp <= inputs.numeric("system.inverter_mppt_max")
                or any(inputs.numeric("system.module_isc") * value > inputs.numeric("system.inverter_max_input_current") for value in allocated_strings)
                or inputs.numeric("system.module_imp") > inputs.numeric("system.module_isc")
                or vmp > voc):
            raise ContractError("ENERGY_ELECTRICAL_CONFIGURATION")
        # Cold/hot voltage coefficients are absent in the frozen facts: do not
        # invent them. The supplied design-check reference remains mandatory.
        reference = inputs.value("layout.string_validation_reference")
        return {"dc_kwp": dc, "ac_kw": ac, "dc_ac_ratio": dc/ac,
            "usable_area_m2": usable, "occupied_area_m2": count*module_area/gcr,
            "module_area_m2": count*module_area, "kwp_per_usable_m2": dc/declared_usable,
            "groups": [{"id": iid, "ac_kw": unit_ac, "dc_kwp": dc*fraction,
                        "efficiency": efficiency} for iid, fraction in zip(ids, allocations)],
            "string_check_reference": reference,
            "electrical_check_scope": "STC_CHECKS_AND_SOURCE_LINKED_TEMPERATURE_DESIGN_REVIEW_NOT_AN_ENGINEERING_APPROVAL"}


def validate_rooftop(inputs):
    if inputs.pv_type != "industrial_rooftop":
        raise ContractError("ENERGY_CATEGORY_MISMATCH")
    if inputs.value("project.has_storage") is not False:
        raise ContractError("ENERGY_STORAGE_NOT_IMPLEMENTED")
    if inputs.numeric("roof.design_added_load") > inputs.numeric("roof.allowable_additional_load"):
        raise ContractError("ENERGY_ROOF_LOAD")
    if inputs.numeric("roof.remaining_life") < inputs.value("project.evaluation_years"):
        raise ContractError("ENERGY_ROOF_LIFE")
    for fid in ("roof.structure_report_id", "roof.fire_access_reference", "roof.waterproof_plan"):
        inputs.value(fid)


def validate_ground(inputs):
    if inputs.pv_type != "utility_scale_ground":
        raise ContractError("ENERGY_CATEGORY_MISMATCH")
    if inputs.value("project.has_storage") is not False:
        raise ContractError("ENERGY_STORAGE_NOT_IMPLEMENTED")
    if inputs.value("project.sales_mode") != "full_export":
        raise ContractError("ENERGY_GROUND_SALES_MODE")
    if not 0 < inputs.numeric("grid.power_factor") <= 1:
        raise ContractError("POWER_FACTOR_DOMAIN", "grid.power_factor")
    for fid in ("site.land_classification", "site.geotechnical_reference", "site.flood_reference"):
        inputs.value(fid)
    # A tracker is not a fixed-POA model without a separately validated method.
    if inputs.value("system.mounting_type") != "FIXED":
        raise ContractError("BLOCKED_METHOD_REVIEW", "system.mounting_type")
