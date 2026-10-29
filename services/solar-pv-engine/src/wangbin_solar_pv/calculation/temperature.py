"""Prepared, source-aware temperature submodel for interval consumers."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..errors import ContractError
from .common import calculated, nonvalue, number, precision_context
from .method_config import MethodConfig


ABSOLUTE_ZERO_C = Decimal("-273.15")
_METHOD_VERSION = "solar-pv-method-config/1.0.0"


def _validated_methods(methods: MethodConfig) -> MethodConfig:
    """Revalidate the mutable payload once at the public preparation boundary."""
    if type(methods) is not MethodConfig:
        raise ContractError("METHOD_CONFIG_REQUIRED")
    return MethodConfig.from_dict(methods.to_dict())


def _required(config: MethodConfig, parameter_id: str):
    return config.require(parameter_id)


@dataclass(frozen=True, slots=True)
class PreparedTemperature:
    """Immutable temperature evaluator detached from its MethodConfig."""

    method: str
    digits: int
    minimum_cell_c: Decimal | None
    maximum_cell_c: Decimal | None
    a: Decimal | None
    b: Decimal | None
    delta_temperature: Decimal | None
    stc_irradiance: Decimal | None
    parameter_ids: tuple[str, ...]
    _source_ids: tuple[tuple[str, str], ...]
    _source_refs: tuple[tuple[str, str], ...]
    _versions: tuple[tuple[str, str], ...]

    @property
    def metadata(self) -> dict:
        """Return detached metadata; no mutable configuration is retained."""
        return {
            "method": self.method,
            "version": _METHOD_VERSION,
            "parameter_ids": list(self.parameter_ids),
            "source_ids": dict(self._source_ids),
            "source_refs": dict(self._source_refs),
            "parameter_versions": dict(self._versions),
        }

    def _details(self, module_temp: Decimal | None = None) -> dict:
        details = self.metadata
        details["module_temp"] = module_temp
        return details

    def _check_inputs(self, poa_kw_m2, ambient_c, wind_m_s, supplied_cell_c):
        poa = number(poa_kw_m2, "poa_kw_m2")
        ambient = number(ambient_c, "ambient_c")
        wind = number(wind_m_s, "wind_m_s")
        if poa < 0:
            raise ContractError("NEGATIVE_INPUT", "poa_kw_m2")
        if ambient < ABSOLUTE_ZERO_C:
            raise ContractError("BELOW_ABSOLUTE_ZERO", "ambient_c")
        if wind < 0:
            raise ContractError("NEGATIVE_INPUT", "wind_m_s")
        supplied = None if supplied_cell_c is None else number(supplied_cell_c, "supplied_cell_c")
        if supplied is not None and supplied < ABSOLUTE_ZERO_C:
            raise ContractError("BELOW_ABSOLUTE_ZERO", "supplied_cell_c")
        return poa, ambient, wind, supplied

    def _check_domain(self, value: Decimal, field_id: str = "cell_temperature_c") -> None:
        if value < ABSOLUTE_ZERO_C:
            raise ContractError("BELOW_ABSOLUTE_ZERO", field_id)
        if self.minimum_cell_c is not None and value < self.minimum_cell_c:
            raise ContractError("THERMAL_MODEL_TEMPERATURE_DOMAIN", field_id)
        if self.maximum_cell_c is not None and value > self.maximum_cell_c:
            raise ContractError("THERMAL_MODEL_TEMPERATURE_DOMAIN", field_id)

    def evaluate(self, poa_kw_m2, ambient_c, wind_m_s, supplied_cell_c=None) -> dict:
        poa, ambient, wind, supplied = self._check_inputs(
            poa_kw_m2, ambient_c, wind_m_s, supplied_cell_c
        )
        if self.method == "NOT_REQUIRED_PR":
            if supplied is not None:
                raise ContractError("SUPPLIED_CELL_NOT_ALLOWED", "thermal.method")
            return nonvalue(
                "NOT_APPLICABLE",
                "THERMAL_MODEL_NOT_REQUIRED_PR",
                details=self._details(None),
            )
        if self.method == "CELL_TEMPERATURE_SUPPLIED":
            if supplied is None:
                raise ContractError("BLOCKED_MISSING_INPUT", "supplied_cell_c")
            with precision_context(self.digits):
                self._check_domain(supplied, "supplied_cell_c")
            return calculated(supplied, details=self._details(None))
        if supplied is not None:
            raise ContractError("SUPPLIED_CELL_NOT_ALLOWED", "supplied_cell_c")

        # Decimal.exp is deliberately evaluated inside the configured local
        # context.  The zero-POA branch is explicit so night is not an
        # accidental ambient-as-cell shortcut.
        with precision_context(self.digits):
            if poa == 0:
                module_temp = ambient
                cell_temp = ambient
            else:
                exponent = self.a + self.b * wind
                module_temp = ambient + (poa * Decimal("1000")) * exponent.exp()
                cell_temp = module_temp + (poa / self.stc_irradiance) * self.delta_temperature
            self._check_domain(module_temp, "module_temp")
            self._check_domain(cell_temp)
            return calculated(cell_temp, details=self._details(module_temp))


def prepare_temperature(methods: MethodConfig) -> PreparedTemperature:
    """Validate a method config once and prepare a row-reusable evaluator."""
    config = _validated_methods(methods)
    method = _required(config, "thermal.method")
    digits = config.require("precision.digits")
    if type(digits) is not int or digits < 34 or digits > 1024:
        raise ContractError("INTEGER_DOMAIN", "precision.digits")

    if method == "SANDIA":
        parameter_ids = (
            "precision.digits",
            "thermal.method",
            "thermal.a",
            "thermal.b",
            "thermal.delta_temperature",
            "thermal.minimum_cell_temperature",
            "thermal.maximum_cell_temperature",
            "constants.stc_irradiance",
        )
    elif method == "CELL_TEMPERATURE_SUPPLIED":
        parameter_ids = (
            "precision.digits",
            "thermal.method",
            "thermal.minimum_cell_temperature",
            "thermal.maximum_cell_temperature",
        )
    elif method == "NOT_REQUIRED_PR":
        parameter_ids = ("precision.digits", "thermal.method")
    else:  # MethodConfig schema is authoritative, this guards forged objects.
        raise ContractError("THERMAL_METHOD_UNSUPPORTED", "thermal.method")

    # Resolve through require before copying evidence so absence/review status
    # remains an explicit BLOCKED_METHOD_REVIEW, never a KeyError.
    values = {pid: _required(config, pid) for pid in parameter_ids}
    evidence = {pid: config.evidence((pid,))[pid] for pid in parameter_ids}
    minimum = number(values["thermal.minimum_cell_temperature"], "thermal.minimum_cell_temperature") if "thermal.minimum_cell_temperature" in values else None
    maximum = number(values["thermal.maximum_cell_temperature"], "thermal.maximum_cell_temperature") if "thermal.maximum_cell_temperature" in values else None
    if minimum is not None and minimum < ABSOLUTE_ZERO_C:
        raise ContractError("BELOW_ABSOLUTE_ZERO", "thermal.minimum_cell_temperature")
    if maximum is not None and maximum < ABSOLUTE_ZERO_C:
        raise ContractError("BELOW_ABSOLUTE_ZERO", "thermal.maximum_cell_temperature")
    if minimum is not None and maximum is not None and minimum >= maximum:
        raise ContractError("METHOD_PARAMETER_ORDER", "thermal.minimum_cell_temperature")

    def decimal_or_none(pid):
        return None if pid not in values else number(values[pid], pid)

    return PreparedTemperature(
        method=method,
        digits=digits,
        minimum_cell_c=minimum,
        maximum_cell_c=maximum,
        a=decimal_or_none("thermal.a"),
        b=decimal_or_none("thermal.b"),
        delta_temperature=decimal_or_none("thermal.delta_temperature"),
        stc_irradiance=decimal_or_none("constants.stc_irradiance"),
        parameter_ids=parameter_ids,
        _source_ids=tuple((pid, evidence[pid]["source_id"]) for pid in parameter_ids),
        _source_refs=tuple((pid, evidence[pid]["source_reference"]) for pid in parameter_ids),
        _versions=tuple((pid, evidence[pid]["version"]) for pid in parameter_ids),
    )


def cell_temperature(
    poa_kw_m2,
    ambient_c,
    wind_m_s,
    *,
    methods: MethodConfig,
    supplied_cell_c=None,
) -> dict:
    """Public one-row wrapper retaining strict configuration revalidation."""
    return prepare_temperature(methods).evaluate(
        poa_kw_m2, ambient_c, wind_m_s, supplied_cell_c=supplied_cell_c
    )
