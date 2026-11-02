"""Shared posting eligibility. See docs/ELIGIBILITY.md for missing-evidence rules."""

from __future__ import annotations

import re
from dataclasses import dataclass

from catalog.io import current_season

from scripts.geo import is_us_location
from scripts.posting_context import placement_evidence, role_evidence
from scripts.qualifications import Qualification, degree_outcome, evidence_text, qualifications

_NON_STEM_RE = re.compile(
    r"\b(?:hr|human resources|people services|people operations|finance|financial|"
    r"accounting|brand manag\w*|marketing|sales|business|recruiting|"
    r"talent acquisition|communications|legal)\b",
    re.I,
)
_STEM_RE = re.compile(
    r"\b(?:engineer\w*|software|firmware|hardware|embedded|robotic\w*|"
    r"scientist\w*|science|scientific|research|biomed\w*|bme|r\s*&\s*d|"
    r"quality|manufacturing|regulatory|laboratory|clinical|chemistry|biology|"
    r"biolog\w*|physics|mathematics|statistics|data|analytics|machine learning|"
    r"cybersecurity|informatics|technical|information[ -]+technology)\b",
    re.I,
)
_BUSINESS_STEM_RE = re.compile(r"\bbusiness (?:intelligence|analytics|systems)\b", re.I)
_INTERN_RE = re.compile(r"\bintern(?:ship)?s?\b", re.I)
_COOP_RE = re.compile(r"\bco[ -]?ops?\b", re.I)
_SUMMER_RE = re.compile(r"\bsummer\b", re.I)
_OFF_SEASON_RE = re.compile(r"\b(?:fall|spring|winter)\b", re.I)
_MULTI_TERM_RE = re.compile(r"\b(?:rotating|multi[ -]?term)\b", re.I)
_YEAR_RE = re.compile(r"\b20\d{2}\b")
_TERM_YEAR_RE = re.compile(
    r"\b(summer|fall|spring|winter)[\s/-]*(?:of\s+)?(20\d{2})\b|"
    r"\b(20\d{2})[\s/-]*(summer|fall|spring|winter)\b",
    re.I,
)
_OFF_TERM_BODY_RE = re.compile(
    r"\b(?:fall|spring|winter)(?:[ -]+only)?\s+(?:intern\w*|co[ -]?op|term|placement)\b|"
    r"\b(?:internship|co[ -]?op|term)\s+(?:is\s+)?(?:in\s+|for\s+)?(?:fall|spring|winter)\b|"
    r"\b(?:rotating|multi[ -]?term)\s+co[ -]?op\b",
    re.I,
)


def posting_evidence(payload: dict) -> dict[str, object]:
    """Retain available description, education, and term fields from JSON adapters.

    Search timestamps, requisition IDs, and graduation dates are not term evidence.
    These fields are transient and do not add properties to the catalog schema.
    """
    fields = {
        "description": (
            "description",
            "descriptionPlain",
            "content",
            "lists",
            "additionalPlain",
            "jobDescription",
            "JobDescription",
            "Description",
            "JobDescriptionStr",
            "jobAd",
            "qualifications",
            "Qualifications",
            "ExternalQualificationsStr",
        ),
        "degree_requirements": (
            "degree",
            "degreeRequirements",
            "degree_requirements",
            "educationRequirements",
            "education",
            "Education",
            "EducationLevel",
        ),
        "season": ("season", "Season", "term", "internshipSeason"),
    }
    return {
        target: {key: payload[key] for key in keys if key in payload}
        for target, keys in fields.items()
    }


@dataclass(frozen=True)
class PostingDecision:
    outcome: str
    reason: str
    qualifications: tuple[Qualification, ...] = ()


def include_posting(*args, **kwargs) -> bool:
    """Compatibility gate: only explicit accept decisions enter the catalog."""
    return classify_posting(*args, **kwargs).outcome == "accept"


def classify_posting(
    title: str,
    location: str,
    *,
    season: str = "",
    target_season: str | None = None,
    degree: object = "",
    degree_requirements: object = "",
    description: object = "",
    short_description: object = "",
) -> PostingDecision:
    """Classify US STEM internships for the target season and BS/MS audience.

    Unknown term/degree is allowed; unknown geography/STEM is not. An unqualified
    year in a title is treated as the intake year; body years require a term.
    """
    evidence = tuple(
        qualifications(title, "title", "required")
        + qualifications(degree, "degree", "required")
        + qualifications(degree_requirements, "degree_requirements", "required")
        + qualifications(description, "description")
        + qualifications(short_description, "short_description")
    )
    title = evidence_text(title)
    body = evidence_text(description)
    short = evidence_text(short_description)
    education = evidence_text(degree_requirements)
    if not is_us_location(location):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    if not (_INTERN_RE.search(title) or _COOP_RE.search(title)):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    if _OFF_SEASON_RE.search(title) or _MULTI_TERM_RE.search(title):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    term = evidence_text(season)
    if _OFF_SEASON_RE.search(term) or _MULTI_TERM_RE.search(term):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    placement = placement_evidence(description) + "\n" + placement_evidence(short_description)
    if _OFF_TERM_BODY_RE.search(placement):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    target = target_season or current_season()
    target_year = _YEAR_RE.search(target)
    if target_year is None:
        raise ValueError(f"target season must contain a year: {target!r}")
    if any(year != target_year[0] for year in _YEAR_RE.findall(f"{title} {term}")):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    for match in _TERM_YEAR_RE.finditer(placement):
        name, year = (match[1], match[2]) if match[1] else (match[4], match[3])
        if name.lower() != "summer" or year != target_year[0]:
            return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    if _COOP_RE.search(title) and not _SUMMER_RE.search(f"{title} {term} {placement}"):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)

    # Clear non-STEM titles win over company boilerplate in a description.
    role_title = _BUSINESS_STEM_RE.sub("data", role_evidence(title).replace("-", " "))
    if _NON_STEM_RE.search(role_title):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    supporting_role = _BUSINESS_STEM_RE.sub("data", role_evidence(f"{body} {short} {education}"))
    # IT is an abbreviation in a role title; description prose often uses the
    # same letters as a pronoun. Supporting prose needs explicit STEM wording.
    stem_title = bool(_STEM_RE.search(role_title) or re.search(r"\bIT\b", role_title))
    if not stem_title and _NON_STEM_RE.search(supporting_role):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)
    if not stem_title and not (_STEM_RE.search(supporting_role) or short == "IT"):
        return PostingDecision("reject", "geography, role, or season outside scope", evidence)

    outcome = degree_outcome(list(evidence))
    reasons = {
        "accept": "in scope",
        "reject": "mandatory doctoral qualification",
        "review": "doctoral qualification meaning or scope unresolved",
    }
    return PostingDecision(outcome, reasons[outcome], evidence)
