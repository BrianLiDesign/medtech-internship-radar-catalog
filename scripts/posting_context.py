"""Select role and placement evidence without borrowing unrelated prose scope."""

from __future__ import annotations

import re

from scripts.qualifications import evidence_text

_TERM = re.compile(
    r"\b(?:summer|fall|spring|winter)(?:[\s/-]+(?:of\s+)?20\d{2})?\b|"
    r"\b20\d{2}[\s/-]+(?:summer|fall|spring|winter)\b",
    re.I,
)
_SUBJECT = re.compile(
    r"\b(?P<graduation>graduation|graduating|graduated|"
    r"graduates?(?=\s+(?:in|by|before|after|during|between|on|from)\b))\b|"
    r"\b(?P<placement>intern(?:ship)?|co[ -]?op|placement|term|position)\b",
    re.I,
)
_GRADUATION_HEADING = re.compile(r"^(?:expected\s+)?graduation(?:\s+date)?\s*:?$", re.I)
_PLACEMENT_HEADING = re.compile(
    r"^(?:internship|co[ -]?op|placement)(?:\s+(?:term|season|dates?))?\s*:?$", re.I
)
_AUTHORIZATION = re.compile(
    r"\blegal\s+(?:(?:U\.?S\.?A?\.?|United States)\s+)?(?:(?:work|employment)\s+)?"
    r"(?:authori[sz]ation|right|eligibility|status|permanent\s+residen(?:t|cy))\b",
    re.I,
)


def _text_fields(value: object):
    """Field order must not make one source inherit another source's subject."""
    if isinstance(value, dict):
        for part in value.values():
            yield from _text_fields(part)
    elif isinstance(value, list):
        for part in value:
            yield from _text_fields(part)
    elif isinstance(value, str):
        yield evidence_text(value)


def placement_evidence(value: object) -> str:
    """Mask graduation-linked seasons while retaining independent placement terms."""
    result = []
    for text in _text_fields(value):
        graduation_heading = False
        for clause in re.split(r"[;\n]|(?<=[.!?])\s+", text):
            clause = clause.strip()
            if _GRADUATION_HEADING.fullmatch(clause):
                graduation_heading = True
                continue
            if _PLACEMENT_HEADING.fullmatch(clause):
                graduation_heading = False
                continue
            if ":" in clause:
                label = clause.split(":", 1)[0]
                graduation_heading = bool(_GRADUATION_HEADING.fullmatch(label))
            masked = clause
            for term in reversed(list(_TERM.finditer(clause))):
                subjects = list(_SUBJECT.finditer(clause[: term.start()]))
                is_graduation = (
                    subjects[-1].lastgroup == "graduation" if subjects else graduation_heading
                )
                # A placement subject immediately after the term is explicit
                # evidence even when a graduation subject occurred earlier.
                if re.match(
                    r"\s+(?:intern(?:ship)?|co[ -]?op|placement|term)\b", clause[term.end() :], re.I
                ):
                    is_graduation = False
                if is_graduation:
                    masked = masked[: term.start()] + " " * len(term[0]) + masked[term.end() :]
            result.append(masked)
    return "\n".join(result)


def role_evidence(value: object) -> str:
    """Mask authorization noun phrases, retaining real legal/finance role evidence."""
    return _AUTHORIZATION.sub(" ", evidence_text(value))
