"""Phase 3B engineering formula kernels.

The module is deliberately value-only: adapters must provide the frozen formula
field IDs, including any normalized units and method evidence.  Indexed values
are represented by ``{stable_id: Decimal}`` and an explicit, exact ID sequence;
this module never uses ``zip`` to hide a missing or extra member.
"""
from __future__ import annotations

from decimal import Decimal

from ..errors import ContractError
from .common import calculated, integer, nonnegative, nonvalue, number, precision_context, ratio


FORMULA_IDS = (
    "F-DC-CAPACITY",
    "F-AC-CAPACITY",
    "F-DC-AC-RATIO",
    "F-POA-IRRADIATION",
    "F-FIRST-YEAR-ENERGY",
    "F-LOSS-COMPOSITE",
    "F-DC-TIME-POWER",
    "F-AC-INVERTER-POWER",
    "F-AVAILABLE-ENERGY",
    "F-ENERGY-AGGREGATION",
    "F-INITIAL-DEGRADATION",
    "F-ANNUAL-DEGRADATION",
    "F-PIECEWISE-DEGRADATION",
    "F-EQUIVALENT-HOURS",
    "F-CAPACITY-FACTOR",
    "F-PR-OBSERVED",
    "F-EXPORT-LIMIT-ENERGY",
    "F-UNIT-KW-MW",
    "F-UNIT-KWH-MWH",
    "F-UNIT-IRRADIANCE-W-KW",
    "F-UNIT-COST-WP-KWP",
    "F-UNIT-DC-CAPACITY",
    "F-UNIT-AC-CAPACITY",
    "F-USABLE-AREA",
    "F-AVERAGE-ANNUAL-ENERGY",
    "F-EMISSIONS-AVOIDED",
    "F-TRANSFORMER-ACTIVE-LIMIT",
)

_REQUIRED_FIELDS = {
    "F-DC-CAPACITY": ("equipment.module_count", "equipment.module_power_kwp"),
    "F-AC-CAPACITY": ("equipment.inverters.rated_ac_kw", "equipment.inverters.ids"),
    "F-DC-AC-RATIO": ("capacity.dc_kwp", "capacity.ac_kw"),
    "F-POA-IRRADIATION": ("resource.poa_irradiance_kw_m2", "time.interval_hours", "time.resource_intervals"),
    "F-FIRST-YEAR-ENERGY": ("capacity.dc_kwp", "resource.poa_irradiation_kwh_m2", "constants.stc_irradiance_kw_m2", "energy.pr_assumed"),
    "F-LOSS-COMPOSITE": ("losses.independent_rates", "losses.active_ids"),
    "F-DC-TIME-POWER": ("capacity.dc_kwp", "resource.effective_poa_kw_m2", "constants.stc_irradiance_kw_m2", "equipment.power_temperature_coefficient", "resource.cell_temperature_c", "constants.stc_cell_temperature_c", "losses.dc_retention"),
    "F-AC-INVERTER-POWER": ("capacity.ac_kw", "losses.inverter_efficiency", "energy.dc_power_kw"),
    "F-AVAILABLE-ENERGY": ("energy.inverter_ac_power_kw", "losses.ac_retention", "losses.transformer_retention", "losses.export_line_retention", "energy.auxiliary_kw", "time.interval_hours", "losses.availability"),
    "F-ENERGY-AGGREGATION": ("energy.boundary_interval_kwh", "energy.boundary_id", "time.aggregation_period", "time.period_interval_ids"),
    "F-INITIAL-DEGRADATION": ("energy.first_year_pre_initial_kwh", "degradation.initial_fraction"),
    "F-ANNUAL-DEGRADATION": ("energy.first_year_ac_kwh", "degradation.annual_fraction", "time.operating_year"),
    "F-PIECEWISE-DEGRADATION": ("degradation.previous_retention", "degradation.yearly_fraction", "degradation.replacement_uplift"),
    "F-EQUIVALENT-HOURS": ("energy.annual_kwh", "energy.reference_capacity_kw"),
    "F-CAPACITY-FACTOR": ("energy.annual_kwh", "energy.reference_capacity_kw", "time.year_hours"),
    "F-PR-OBSERVED": ("energy.annual_kwh", "capacity.dc_kwp", "resource.poa_irradiation_kwh_m2", "constants.stc_irradiance_kw_m2"),
    "F-EXPORT-LIMIT-ENERGY": ("grid.export_limit_kw", "time.interval_hours"),
    "F-UNIT-KW-MW": ("units.power_kw", "constants.kilo_scale"),
    "F-UNIT-KWH-MWH": ("units.energy_kwh", "constants.kilo_scale"),
    "F-UNIT-IRRADIANCE-W-KW": ("units.irradiance_w_m2", "constants.kilo_scale"),
    "F-UNIT-COST-WP-KWP": ("units.cost_per_wp", "constants.kilo_scale"),
    "F-UNIT-DC-CAPACITY": ("capacity.dc_kwp", "constants.kilo_scale"),
    "F-UNIT-AC-CAPACITY": ("capacity.ac_kw", "constants.kilo_scale"),
    "F-USABLE-AREA": ("site.total_area", "site.exclusion_area"),
    "F-AVERAGE-ANNUAL-ENERGY": ("energy.annual_kwh", "time.operating_year_count"),
    "F-EMISSIONS-AVOIDED": ("environment.eligible_energy", "environment.grid_emission_factor"),
    "F-TRANSFORMER-ACTIVE-LIMIT": ("grid.transformer_capacity", "grid.power_factor"),
}

_ALLOWED_OPTION_KEYS = {"precision_digits", "applicable", "index_ids"}


def evaluate(formula_id, values, options=None):
    """Evaluate one engineering kernel under the exact-number contract."""
    if type(formula_id) is not str or formula_id not in FORMULA_IDS:
        raise ContractError("UNKNOWN_FORMULA", formula_id if isinstance(formula_id, str) else None)
    options = _options(options)
    if options.get("applicable", True) is False:
        return nonvalue("NOT_APPLICABLE", "EXPLICITLY_NOT_APPLICABLE", details={"formula_id": formula_id})
    if not isinstance(values, dict):
        raise ContractError("FORMULA_VALUES_MAPPING_REQUIRED", formula_id)
    required = set(_REQUIRED_FIELDS[formula_id])
    actual = set(values)
    if actual != required:
        missing = required - actual
        if missing:
            return nonvalue("BLOCKED_MISSING_INPUT", "BLOCKED_MISSING_INPUT", details={"formula_id": formula_id, "missing_field_ids": sorted(missing)})
        raise ContractError("FORMULA_VALUES_KEYS", formula_id)
    nested_missing = _find_none(values)
    if nested_missing is not None:
        return nonvalue("BLOCKED_MISSING_INPUT", "BLOCKED_MISSING_INPUT", details={"formula_id": formula_id, "missing_field_ids": [nested_missing]})
    precision_digits = options.get("precision_digits", 80)
    with precision_context(precision_digits):
        value = _DISPATCH[formula_id](values, options)
    if isinstance(value, dict) and "status" in value:
        return value
    return calculated(value, details={"formula_id": formula_id, "precision_digits": precision_digits})


def _options(options):
    if options is None:
        return {}
    if not isinstance(options, dict):
        raise ContractError("OPTIONS_MAPPING_REQUIRED")
    extra = set(options) - _ALLOWED_OPTION_KEYS
    if extra:
        raise ContractError("OPTIONS_KEYS")
    if "applicable" in options and type(options["applicable"]) is not bool:
        raise ContractError("APPLICABILITY_BOOLEAN_REQUIRED")
    if "precision_digits" in options:
        integer(options["precision_digits"], "precision.precision_digits", minimum=34, maximum=1024)
    if "index_ids" in options:
        if not isinstance(options["index_ids"], dict):
            raise ContractError("INDEX_IDS_MAPPING_REQUIRED")
        for field_id, ids in options["index_ids"].items():
            if not isinstance(field_id, str):
                raise ContractError("INDEX_FIELD_ID_REQUIRED")
            _validate_ids(ids, field_id)
    return options


def _find_none(value, field_id=None):
    if value is None:
        return field_id or "<values>"
    if isinstance(value, dict):
        for key, child in value.items():
            found = _find_none(child, str(key))
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for child in value:
            found = _find_none(child, field_id)
            if found is not None:
                return found
    return None


def _validate_ids(ids, field_id):
    if not isinstance(ids, (list, tuple)):
        raise ContractError("INDEX_IDS_SEQUENCE_REQUIRED", field_id)
    seen = set()
    for item in ids:
        if type(item) is not str or not item:
            raise ContractError("STABLE_INDEX_ID_REQUIRED", field_id)
        if item in seen:
            raise ContractError("DUPLICATE_INDEX_ID", field_id)
        seen.add(item)
    return tuple(ids)


def _indexed(values, map_field, ids_field, options):
    ids = _validate_ids(values[ids_field], ids_field)
    mapping = values[map_field]
    if not isinstance(mapping, dict):
        raise ContractError("INDEXED_DECIMAL_MAPPING_REQUIRED", map_field)
    if any(type(key) is not str or not key for key in mapping):
        raise ContractError("STABLE_INDEX_ID_REQUIRED", map_field)
    if set(mapping) != set(ids):
        raise ContractError("INDEX_SET_MISMATCH", map_field)
    return [(item, nonnegative(number(mapping[item], map_field), map_field)) for item in ids]


def _indexed_option(values, map_field, options):
    index_ids = options.get("index_ids", {})
    if not isinstance(index_ids, dict) or map_field not in index_ids:
        raise ContractError("INDEX_IDS_REQUIRED", map_field)
    ids = _validate_ids(index_ids[map_field], map_field)
    mapping = values[map_field]
    if not isinstance(mapping, dict):
        raise ContractError("INDEXED_DECIMAL_MAPPING_REQUIRED", map_field)
    if any(type(key) is not str or not key for key in mapping):
        raise ContractError("STABLE_INDEX_ID_REQUIRED", map_field)
    if set(mapping) != set(ids):
        raise ContractError("INDEX_SET_MISMATCH", map_field)
    return [(item, nonnegative(number(mapping[item], map_field), map_field)) for item in ids]


def _label(value, field_id):
    if type(value) is not str or not value:
        raise ContractError("STABLE_LABEL_REQUIRED", field_id)
    return value


def _positive(value, field_id):
    value = number(value, field_id)
    if value <= 0:
        raise ContractError("POSITIVE_NUMBER_REQUIRED", field_id)
    return value


def _ratio(value, field_id):
    return ratio(value, field_id)


def _definition_constant(value, expected, field_id):
    value = number(value, field_id)
    if value != expected:
        raise ContractError("CONSTANT_DEFINITION", field_id)
    return value


def _undefined(formula_id, reason):
    return nonvalue("UNDEFINED", reason, details={"formula_id": formula_id})


def _dc_capacity(v, _):
    count = integer(v["equipment.module_count"], "equipment.module_count", minimum=0)
    power = _positive(v["equipment.module_power_kwp"], "equipment.module_power_kwp")
    return Decimal(count) * power


def _ac_capacity(v, _):
    indexed = _indexed(v, "equipment.inverters.rated_ac_kw", "equipment.inverters.ids", _)
    if not indexed:
        raise ContractError("NONEMPTY_INDEX_SET_REQUIRED", "equipment.inverters.ids")
    return sum((value for _, value in indexed), Decimal(0))


def _dc_ac_ratio(v, _):
    dc = nonnegative(v["capacity.dc_kwp"], "capacity.dc_kwp")
    ac = nonnegative(v["capacity.ac_kw"], "capacity.ac_kw")
    if ac == 0:
        return _undefined("F-DC-AC-RATIO", "ZERO_DENOMINATOR")
    return dc / ac


def _poa(v, _):
    irradiance = _indexed(v, "resource.poa_irradiance_kw_m2", "time.resource_intervals", _)
    intervals = _indexed(v, "time.interval_hours", "time.resource_intervals", _)
    interval_values = dict(intervals)
    if any(value <= 0 for value in interval_values.values()):
        raise ContractError("INTERVAL_DURATION_DOMAIN", "time.interval_hours")
    return sum((value * interval_values[item] for item, value in irradiance), Decimal(0))


def _first_year(v, _):
    dc = nonnegative(v["capacity.dc_kwp"], "capacity.dc_kwp")
    poa = nonnegative(v["resource.poa_irradiation_kwh_m2"], "resource.poa_irradiation_kwh_m2")
    stc = _definition_constant(v["constants.stc_irradiance_kw_m2"], 1, "constants.stc_irradiance_kw_m2")
    # PR is not an independent loss fraction. The selected D2 model validates
    # its declared applicability bounds and may legitimately allow PR > 1.
    pr = nonnegative(v["energy.pr_assumed"], "energy.pr_assumed")
    return dc * (poa / stc) * pr


def _loss(v, _):
    indexed = _indexed(v, "losses.independent_rates", "losses.active_ids", _)
    result = Decimal(1)
    for _, loss_rate in indexed:
        result *= Decimal(1) - _ratio(loss_rate, "losses.independent_rates")
    return result


def _dc_time_power(v, _):
    dc = nonnegative(v["capacity.dc_kwp"], "capacity.dc_kwp")
    poa = nonnegative(v["resource.effective_poa_kw_m2"], "resource.effective_poa_kw_m2")
    stc = _definition_constant(v["constants.stc_irradiance_kw_m2"], 1, "constants.stc_irradiance_kw_m2")
    gamma = number(v["equipment.power_temperature_coefficient"], "equipment.power_temperature_coefficient")
    cell = number(v["resource.cell_temperature_c"], "resource.cell_temperature_c")
    stc_cell = number(v["constants.stc_cell_temperature_c"], "constants.stc_cell_temperature_c")
    retention = _ratio(v["losses.dc_retention"], "losses.dc_retention")
    temperature_factor = Decimal(1) + gamma * (cell - stc_cell)
    if temperature_factor < 0:
        raise ContractError("TEMPERATURE_POWER_FACTOR_DOMAIN", "resource.cell_temperature_c")
    raw = dc * (poa / stc) * temperature_factor * retention
    return max(Decimal(0), raw)


def _ac_inverter_power(v, _):
    capacity = nonnegative(v["capacity.ac_kw"], "capacity.ac_kw")
    efficiency = _ratio(v["losses.inverter_efficiency"], "losses.inverter_efficiency")
    dc_power = nonnegative(v["energy.dc_power_kw"], "energy.dc_power_kw")
    return min(capacity, max(Decimal(0), efficiency * dc_power))


def _available_energy(v, _):
    ac = nonnegative(v["energy.inverter_ac_power_kw"], "energy.inverter_ac_power_kw")
    ac_retention = _ratio(v["losses.ac_retention"], "losses.ac_retention")
    transformer = _ratio(v["losses.transformer_retention"], "losses.transformer_retention")
    line = _ratio(v["losses.export_line_retention"], "losses.export_line_retention")
    auxiliary = nonnegative(v["energy.auxiliary_kw"], "energy.auxiliary_kw")
    hours = _positive(v["time.interval_hours"], "time.interval_hours")
    availability = _ratio(v["losses.availability"], "losses.availability")
    return max(Decimal(0), (ac * ac_retention * transformer * line - auxiliary) * hours * availability)


def _aggregation(v, _):
    _label(v["energy.boundary_id"], "energy.boundary_id")
    _label(v["time.aggregation_period"], "time.aggregation_period")
    ids = _validate_ids(v["time.period_interval_ids"], "time.period_interval_ids")
    mapping = v["energy.boundary_interval_kwh"]
    if not isinstance(mapping, dict):
        raise ContractError("INDEXED_DECIMAL_MAPPING_REQUIRED", "energy.boundary_interval_kwh")
    if set(mapping) != set(ids):
        raise ContractError("INDEX_SET_MISMATCH", "energy.boundary_interval_kwh")
    return sum((nonnegative(number(mapping[item], "energy.boundary_interval_kwh"), "energy.boundary_interval_kwh") for item in ids), Decimal(0))


def _initial(v, _):
    energy = nonnegative(v["energy.first_year_pre_initial_kwh"], "energy.first_year_pre_initial_kwh")
    initial = _ratio(v["degradation.initial_fraction"], "degradation.initial_fraction")
    return energy * (Decimal(1) - initial)


def _annual(v, _):
    energy = nonnegative(v["energy.first_year_ac_kwh"], "energy.first_year_ac_kwh")
    degradation = v["degradation.annual_fraction"]
    degradation = number(degradation, "degradation.annual_fraction")
    if degradation < 0 or degradation >= 1:
        raise ContractError("ANNUAL_DEGRADATION_DOMAIN", "degradation.annual_fraction")
    year = integer(v["time.operating_year"], "time.operating_year", minimum=1)
    return energy * (Decimal(1) - degradation) ** (year - 1)


def _piecewise(v, _):
    previous = nonnegative(v["degradation.previous_retention"], "degradation.previous_retention")
    yearly = _ratio(v["degradation.yearly_fraction"], "degradation.yearly_fraction")
    uplift = nonnegative(v["degradation.replacement_uplift"], "degradation.replacement_uplift")
    return previous * (Decimal(1) - yearly) + uplift


def _equivalent_hours(v, _):
    energy = nonnegative(v["energy.annual_kwh"], "energy.annual_kwh")
    capacity = nonnegative(v["energy.reference_capacity_kw"], "energy.reference_capacity_kw")
    if capacity == 0:
        return _undefined("F-EQUIVALENT-HOURS", "ZERO_DENOMINATOR")
    return energy / capacity


def _capacity_factor(v, _):
    energy = nonnegative(v["energy.annual_kwh"], "energy.annual_kwh")
    capacity = nonnegative(v["energy.reference_capacity_kw"], "energy.reference_capacity_kw")
    hours = nonnegative(v["time.year_hours"], "time.year_hours")
    if capacity == 0 or hours == 0:
        return _undefined("F-CAPACITY-FACTOR", "ZERO_DENOMINATOR")
    return energy / (capacity * hours)


def _pr_observed(v, _):
    energy = nonnegative(v["energy.annual_kwh"], "energy.annual_kwh")
    dc = nonnegative(v["capacity.dc_kwp"], "capacity.dc_kwp")
    poa = nonnegative(v["resource.poa_irradiation_kwh_m2"], "resource.poa_irradiation_kwh_m2")
    stc = _definition_constant(v["constants.stc_irradiance_kw_m2"], 1, "constants.stc_irradiance_kw_m2")
    if dc == 0 or poa == 0:
        return _undefined("F-PR-OBSERVED", "ZERO_DENOMINATOR")
    return (energy / dc) / (poa / stc)


def _export_limit(v, _):
    limit = nonnegative(v["grid.export_limit_kw"], "grid.export_limit_kw")
    hours = _positive(v["time.interval_hours"], "time.interval_hours")
    return limit * hours


def _unit_division(v, source_field):
    source = nonnegative(v[source_field], source_field)
    scale = _definition_constant(v["constants.kilo_scale"], 1000, "constants.kilo_scale")
    return source / scale


def _unit_cost(v, _):
    source = nonnegative(v["units.cost_per_wp"], "units.cost_per_wp")
    scale = _definition_constant(v["constants.kilo_scale"], 1000, "constants.kilo_scale")
    return source * scale


def _usable_area(v, options):
    total = nonnegative(v["site.total_area"], "site.total_area")
    exclusions = _indexed_option(v, "site.exclusion_area", options)
    excluded = sum((value for _, value in exclusions), Decimal(0))
    if excluded > total:
        raise ContractError("EXCLUSION_EXCEEDS_TOTAL", "site.exclusion_area")
    return total - excluded


def _average_annual(v, options):
    years = integer(v["time.operating_year_count"], "time.operating_year_count", minimum=1)
    annual = _indexed_option(v, "energy.annual_kwh", options)
    if len(annual) != years:
        raise ContractError("INDEX_COUNT_MISMATCH", "time.operating_year_count")
    return sum((value for _, value in annual), Decimal(0)) / Decimal(years)


def _emissions(v, _):
    energy = nonnegative(v["environment.eligible_energy"], "environment.eligible_energy")
    factor = nonnegative(v["environment.grid_emission_factor"], "environment.grid_emission_factor")
    return energy * factor


def _transformer(v, _):
    capacity = nonnegative(v["grid.transformer_capacity"], "grid.transformer_capacity")
    power_factor = number(v["grid.power_factor"], "grid.power_factor")
    if power_factor <= 0 or power_factor > 1:
        raise ContractError("POWER_FACTOR_DOMAIN", "grid.power_factor")
    return capacity * power_factor


_DISPATCH = {
    "F-DC-CAPACITY": _dc_capacity,
    "F-AC-CAPACITY": _ac_capacity,
    "F-DC-AC-RATIO": _dc_ac_ratio,
    "F-POA-IRRADIATION": _poa,
    "F-FIRST-YEAR-ENERGY": _first_year,
    "F-LOSS-COMPOSITE": _loss,
    "F-DC-TIME-POWER": _dc_time_power,
    "F-AC-INVERTER-POWER": _ac_inverter_power,
    "F-AVAILABLE-ENERGY": _available_energy,
    "F-ENERGY-AGGREGATION": _aggregation,
    "F-INITIAL-DEGRADATION": _initial,
    "F-ANNUAL-DEGRADATION": _annual,
    "F-PIECEWISE-DEGRADATION": _piecewise,
    "F-EQUIVALENT-HOURS": _equivalent_hours,
    "F-CAPACITY-FACTOR": _capacity_factor,
    "F-PR-OBSERVED": _pr_observed,
    "F-EXPORT-LIMIT-ENERGY": _export_limit,
    "F-UNIT-KW-MW": lambda v, _: _unit_division(v, "units.power_kw"),
    "F-UNIT-KWH-MWH": lambda v, _: _unit_division(v, "units.energy_kwh"),
    "F-UNIT-IRRADIANCE-W-KW": lambda v, _: _unit_division(v, "units.irradiance_w_m2"),
    "F-UNIT-COST-WP-KWP": _unit_cost,
    "F-UNIT-DC-CAPACITY": lambda v, _: _unit_division(v, "capacity.dc_kwp"),
    "F-UNIT-AC-CAPACITY": lambda v, _: _unit_division(v, "capacity.ac_kw"),
    "F-USABLE-AREA": _usable_area,
    "F-AVERAGE-ANNUAL-ENERGY": _average_annual,
    "F-EMISSIONS-AVOIDED": _emissions,
    "F-TRANSFORMER-ACTIVE-LIMIT": _transformer,
}
