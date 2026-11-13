"""Validation reports with stable machine and terminal representations."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterable
from .table import Column, render
from .jsonio import pretty

@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    message: str
    severity: str = "error"

    def __post_init__(self) -> None:
        if self.severity not in {"info","warning","error"}:
            raise ValueError("unknown severity")
        if not self.code or not self.message:
            raise ValueError("findings require a code and message")

    def document(self) -> dict[str,str]:
        return {"code":self.code,"path":self.path,"message":self.message,"severity":self.severity}

@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    checked: int = 0

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def add(self,code: str,path: str,message: str,severity: str = "error") -> None:
        self.findings.append(Finding(code,path,message,severity))

    def merge(self,other: Report,prefix: str = "") -> None:
        self.checked += other.checked
        self.findings.extend(Finding(f.code,prefix+f.path,f.message,f.severity)
                             for f in other.findings)

    def document(self) -> dict[str,object]:
        return {"ok":self.ok,"checked":self.checked,
                "findings":[finding.document() for finding in self.findings]}

    def json(self) -> str:
        return pretty(self.document())

    def table(self) -> str:
        columns = (Column("severity","LEVEL",8),Column("code","CODE",20),
                   Column("path","PATH",40),Column("message","MESSAGE",80))
        return render([f.document() for f in self.findings],columns)

    def counts(self) -> dict[str,int]:
        result = {"info":0,"warning":0,"error":0}
        for finding in self.findings:
            result[finding.severity] += 1
        return result

def combine(reports: Iterable[Report]) -> Report:
    result = Report()
    for report in reports:
        result.merge(report)
    return result
