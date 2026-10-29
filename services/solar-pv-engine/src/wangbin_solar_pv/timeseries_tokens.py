"""Private bounded JSON decoding that retains canonical numeric token spellings.

Phase 2 loads deliberately uses plain Decimal; changing that API is forbidden.
A new bundle must also round-trip legacy float spellings such as 1e-05 without
silently changing its canonical array hash into Decimal's 0.00001 spelling.
"""
from decimal import Decimal
import json

from .errors import ContractError
from .serialization import MAX_JSON_BYTES, _pairs, _invalid_constant, _check


class _TokenDecimal(Decimal):
    __slots__ = ('_token',)

    def __new__(cls, token):
        result = super().__new__(cls, token)
        result._token = token
        return result

    def __str__(self):
        return self._token

    def __setattr__(self, name, value):
        if name == '_token' and not hasattr(self, '_token'):
            return super().__setattr__(name, value)
        raise AttributeError('immutable numeric token')

    def __deepcopy__(self, memo):
        return type(self)(self._token)


def loads(text, *, max_bytes=MAX_JSON_BYTES):
    try:
        if isinstance(text, bytes):
            if len(text) > max_bytes:
                raise ContractError('BUNDLE_FILE_LIMIT')
            text = text.decode('utf-8-sig', errors='strict')
        if len(text.encode('utf-8')) > max_bytes:
            raise ContractError('BUNDLE_FILE_LIMIT')
        value = json.loads(text,parse_float=_TokenDecimal,object_pairs_hook=_pairs,parse_constant=_invalid_constant)
        _check(value)
        return value
    except ContractError:
        raise
    except (ValueError,UnicodeError,RecursionError,OverflowError):
        raise ContractError('BUNDLE_INVALID') from None
