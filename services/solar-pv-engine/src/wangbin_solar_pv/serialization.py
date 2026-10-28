"""Bounded strict JSON with exact decimal numeric tokens and no duplicate keys."""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
import math

from .errors import ContractError

MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_DEPTH = 64


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ContractError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _invalid_constant(_):
    raise ContractError("NON_FINITE_NUMBER")


def _check(value, depth=0):
    if depth > MAX_DEPTH:
        raise ContractError("JSON_DEPTH_LIMIT")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ContractError("NON_FINITE_NUMBER")
        if len(value.as_tuple().digits) > 1024 or abs(value.adjusted()) > 10000:
            raise ContractError("NUMBER_SIZE_LIMIT")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ContractError("NON_FINITE_NUMBER")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError("JSON_STRING_KEYS_REQUIRED")
            _check(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check(item, depth + 1)
    elif value is not None and not isinstance(value, (str, bool, int, float)):
        raise ContractError("NOT_JSON_SERIALIZABLE")


def loads(text: str | bytes, *, max_bytes: int = MAX_JSON_BYTES):
    try:
        if isinstance(text, bytes):
            if len(text) > max_bytes:
                raise ContractError("JSON_SIZE_LIMIT")
            text = text.decode("utf-8-sig", errors="strict")
        if len(text.encode("utf-8")) > max_bytes:
            raise ContractError("JSON_SIZE_LIMIT")
        value = json.loads(text, parse_float=Decimal, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
        _check(value)
        return value
    except ContractError:
        raise
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ContractError("INVALID_JSON") from exc


def dumps(value) -> str:
    _check(value)

    def encode(item):
        if item is None:
            return "null"
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, Decimal):
            return str(item)
        if isinstance(item, (int, float)):
            return json.dumps(item, allow_nan=False)
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, list):
            return "[" + ",".join(encode(v) for v in item) + "]"
        return "{" + ",".join(encode(k) + ":" + encode(item[k]) for k in sorted(item)) + "}"

    text = encode(value)
    if len(text.encode("utf-8")) > MAX_JSON_BYTES:
        raise ContractError("JSON_SIZE_LIMIT")
    return text


def digest(value) -> str:
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()
