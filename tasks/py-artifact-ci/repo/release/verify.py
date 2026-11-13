"""Release gates check archive integrity and project-required members."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from recordkit.archive import unpack
from recordkit.report import Report

@dataclass(frozen=True)
class Required:
    name: str
    minimum_bytes: int = 0
    executable: bool | None = None

def verify(raw: bytes, required: list[Required]) -> Report:
    report=Report()
    try:
        members={row.name:row for row in unpack(raw)}
    except ValueError as exc:
        report.add("BUNDLE_INVALID","",str(exc))
        return report
    for requirement in required:
        report.checked+=1
        member=members.get(requirement.name)
        if member is None:
            report.add("MISSING_MEMBER",requirement.name,"required member missing from release bundle")
        elif len(member.data)<requirement.minimum_bytes:
            report.add("MEMBER_TOO_SMALL",requirement.name,"member is smaller than expected")
        elif requirement.executable is not None and member.executable!=requirement.executable:
            report.add("BAD_MODE",requirement.name,"executable mode does not match release contract")
    return report
