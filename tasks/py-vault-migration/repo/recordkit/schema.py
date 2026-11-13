"""Composable validation for recordkit's command manifests and sidecars."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import Any
from copy import deepcopy
from .validation import Invalid

Validator = Callable[[Any,str],Any]

@dataclass(frozen=True)
class Field:
    validate: Validator
    required: bool = True
    default: Any = None

def string(value: Any,path: str) -> str:
    if not isinstance(value,str):
        raise Invalid(path,"string")
    return value

def number(value: Any,path: str) -> int | float:
    import math
    if type(value) not in (int,float) or not math.isfinite(value):
        raise Invalid(path,"finite number")
    return value

def boolean(value: Any,path: str) -> bool:
    if type(value) is not bool:
        raise Invalid(path,"boolean")
    return value

def literal(expected: Any) -> Validator:
    def check(value: Any,path: str) -> Any:
        if type(value) is not type(expected) or value!=expected:
            raise Invalid(path,repr(expected))
        return value
    return check

def nullable(validate: Validator) -> Validator:
    def check(value: Any,path: str) -> Any:
        return None if value is None else validate(value,path)
    return check

def array(validate: Validator,unique: bool = False) -> Validator:
    def check(value: Any,path: str) -> list[Any]:
        if not isinstance(value,list):
            raise Invalid(path,"array")
        result=[validate(item,f"{path}[{i}]") for i,item in enumerate(value)]
        if unique:
            from .jsonio import canonical
            keys=[canonical(item) for item in result]
            if len(set(keys))!=len(keys):
                raise Invalid(path,"unique array entries")
        return result
    return check

def dictionary(validate: Validator) -> Validator:
    def check(value: Any,path: str) -> dict[str,Any]:
        if not isinstance(value,dict) or not all(isinstance(key,str) for key in value):
            raise Invalid(path,"object with string keys")
        return {key:validate(item,f"{path}.{key}") for key,item in value.items()}
    return check

def one_of(*validators: Validator) -> Validator:
    if not validators:
        raise ValueError("union requires at least one branch")
    def check(value: Any,path: str) -> Any:
        for validate in validators:
            try:
                return validate(value,path)
            except Invalid:
                continue
        raise Invalid(path,"one of the union branches")
    return check

def record(fields: Mapping[str,Field],unknown: str = "reject") -> Validator:
    if unknown not in {"reject","preserve","drop"}:
        raise ValueError("unknown field policy")
    def check(value: Any,path: str) -> dict[str,Any]:
        if not isinstance(value,dict) or not all(isinstance(key,str) for key in value):
            raise Invalid(path,"object")
        result={}
        for key,field in fields.items():
            if key not in value:
                if field.required:
                    raise Invalid(f"{path}.{key}","present field")
                result[key]=deepcopy(field.default)
            else:
                result[key]=field.validate(value[key],f"{path}.{key}")
        for key in value.keys()-fields.keys():
            if unknown=="reject":
                raise Invalid(f"{path}.{key}","known field")
            if unknown=="preserve":
                result[key]=deepcopy(value[key])
        return result
    return check

def bounded(minimum: int | float,maximum: int | float) -> Validator:
    if maximum<minimum:
        raise ValueError("inverted bounds")
    def check(value: Any,path: str) -> int | float:
        value=number(value,path)
        if value<minimum or value>maximum:
            raise Invalid(path,f"number in [{minimum},{maximum}]")
        return value
    return check

def transform(validate: Validator,convert: Callable[[Any],Any]) -> Validator:
    def check(value: Any,path: str) -> Any:
        return convert(validate(value,path))
    return check

def validate(value: Any,schema: Validator) -> Any:
    return schema(value,"$")
