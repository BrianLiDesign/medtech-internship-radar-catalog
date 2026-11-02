"""Clause-scoped qualification evidence, with conservative uncertainty handling.

This is a bounded grammar, not a general prose interpreter. Unresolved credential
relations remain review evidence instead of becoming inferred alternatives.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {
            "p",
            "li",
            "div",
            "br",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "tr",
            "td",
            "th",
            "section",
            "article",
            "ul",
            "ol",
            "blockquote",
        }:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        self.handle_starttag(tag, [])

    def handle_data(self, data):
        self.parts.append(data)


def evidence_text(value: object) -> str:
    """Normalize block boundaries while keeping inline credential text intact."""
    if isinstance(value, dict):
        return "\n".join(evidence_text(part) for part in value.values())
    if isinstance(value, list):
        return "\n".join(evidence_text(part) for part in value)
    if not isinstance(value, str):
        return ""
    parser = _Text()
    parser.feed(unescape(value))
    return "\n".join(" ".join(line.split()) for line in "".join(parser.parts).splitlines()).strip()


_CREDENTIAL = re.compile(
    r"\b(?:ph\.?\s?d\.?|doctoral|doctorate|b\.?s\.?|m\.?s\.?|bsc|msc|"
    r"bachelor(?:['’]s)?|master(?:['’]s)?|undergraduate)(?!\w)",
    re.I,
)
_OFFICE = re.compile(r"\bMS\s+(?:Office|Excel|Word|PowerPoint|Outlook)\b", re.I)
_REQUIRED = re.compile(
    r"\b(?:required|requires?|must|only|pursuing|enrolled|candidate|students?)\b", re.I
)
_PREFERRED = re.compile(r"\b(?:preferred|prefer(?:red|ably)?|desired|a plus|nice to have)\b", re.I)
_UNCERTAIN = re.compile(
    r"\b(?:may|might|depending|unless|equivalent|either required or preferred)\b", re.I
)
_HEADING = re.compile(
    r"^(?:(required|minimum|basic|preferred|desired)\s+)?"
    r"(?:qualifications?|requirements?|education|skills?)\s*:?$",
    re.I,
)
_SPLIT = re.compile(r"\s*\b(?:and(?!/or)|with|but)\b\s*(?!or\b)", re.I)
_COLLEAGUE_RELATION = re.compile(r"\b(?:work(?:ing)?|collaborat(?:e|ing))\s+with\b", re.I)


@dataclass(frozen=True)
class Qualification:
    source: str
    clause: str
    credentials: tuple[str, ...]
    modality: str  # required, preferred, optional, mentioned, unknown
    alternatives: bool = False
    uncertain: bool = False
    source_clause: str = ""
    skill: str | None = None


def _matches(text: str):
    # Mask product names without changing token offsets.
    masked = _OFFICE.sub(lambda match: " " * len(match[0]), text)
    return list(_CREDENTIAL.finditer(masked))


def _credential(token: str) -> str:
    token = token.lower().replace(".", "").replace(" ", "")
    if token.startswith(("ph", "doctor")):
        return "PhD"
    return "MS" if token.startswith(("m",)) else "BS"


def _modality(text: str, inherited: str) -> str:
    relation = _COLLEAGUE_RELATION.search(text)
    if relation and _matches(text) and not _matches(text[: relation.start()]):
        return "mentioned"
    if re.search(r"\b(?:not|never|isn['’]t|aren['’]t)\s+(?:an?\s+)?optional\b", text, re.I):
        return "required"
    if re.search(r"\b(?:not\s+required|optional)\b", text, re.I):
        return "optional"
    if re.search(r"\bnot\s+preferred\b", text, re.I):
        return "unknown"
    if _PREFERRED.search(text):
        return "preferred"
    if _REQUIRED.search(text):
        return "required"
    return inherited


def _fragments(sentence: str) -> list[str]:
    """Split coordinated subjects, preserving relational 'work with' phrases."""
    # A comma between independently modalized skill/degree subjects is a
    # qualification boundary. Commas inside credential alternatives are not.
    for comma in reversed(list(re.finditer(",", sentence))):
        left, right = sentence[: comma.start()], sentence[comma.end() :]
        if (
            re.search(r"\b(?:required|preferred|must|optional)\b", left, re.I)
            and re.search(r"\b(?:required|preferred|must|optional)\b", right, re.I)
            and (not _matches(left) or not _matches(right))
        ):
            sentence = left + ";" + right
    fragments = []
    for chunk in sentence.split(";"):
        fragments.extend(_coordinated_fragments(chunk))
    return fragments


def _coordinated_fragments(sentence: str) -> list[str]:
    fragments = []
    start = 0
    degrees = _matches(sentence)
    alternative_links = [
        (left.end(), right.start())
        for left, right in zip(degrees, degrees[1:])
        if _alternative_link(sentence[left.end() : right.start()])
    ]
    for match in _SPLIT.finditer(sentence):
        if any(left <= match.start() < right for left, right in alternative_links):
            continue
        prefix = sentence[start : match.start()]
        if match[0].strip().lower() == "with" and re.search(
            r"\b(?:work(?:ing)?|collaborat(?:e|ing))\s*$", prefix, re.I
        ):
            continue
        fragments.append(prefix)
        start = match.end()
    fragments.append(sentence[start:])
    scoped = []
    for fragment in fragments:
        relation = _COLLEAGUE_RELATION.search(fragment)
        if relation and _matches(fragment[: relation.start()]):
            # An applicant credential before the relation belongs to a different
            # participant than credentials of the people they will work with.
            scoped.extend([fragment[: relation.start()], fragment[relation.start() :]])
        else:
            scoped.append(fragment)
    return scoped


def _alternative_link(link: str) -> bool:
    """Recognize a connector with an optional degree/discipline noun phrase.

    Do not admit predicates or independent qualifications in a discipline tail:
    a nearby completed degree is not an alternative applicant audience.
    """
    if _REQUIRED.search(link) or re.search(
        r"\b(?:completed|previously|prior|experience|preferred|optional)\b", link, re.I
    ):
        return False
    return bool(
        re.fullmatch(
            r"\s*(?:degree\s*)?(?:in\s+[\w &/()-]+?\s*)?"
            r"(?:/|,|,?\s*or|and/or)\s*(?:an?\s+)?",
            link,
            re.I,
        )
    )


def _sentences(text: str) -> list[str]:
    """Segment original text without cutting inside dotted degree tokens."""
    abbreviations = [
        (match.start(), match.end()) for match in _matches(text) if "." in match[0][:-1]
    ]
    sentences = []
    start = 0
    for boundary in re.finditer(r"[;\n]|(?<=[.!?])\s+", text):
        if any(
            left < boundary.start() < right
            or (boundary.start() == right and not boundary[0].strip() and "\n" not in boundary[0])
            for left, right in abbreviations
        ):
            continue
        sentences.append(text[start : boundary.start()])
        start = boundary.end()
    sentences.append(text[start:])
    return sentences


def _leaves(value: object, source: str, inherited: str):
    """Keep field/list boundaries and explicit section labels as evidence."""
    if isinstance(value, dict):
        # Lever's labeled list content and similar ATS section objects.
        label = value.get("text") or value.get("title") or value.get("name")
        heading = _HEADING.fullmatch(evidence_text(label)) if isinstance(label, str) else None
        if heading and "content" in value:
            inherited = (
                "preferred"
                if (heading[1] or "").lower() in {"preferred", "desired"}
                else "required"
            )
            yield from _leaves(value["content"], source + ".content", inherited)
        else:
            for key, part in value.items():
                heading = _HEADING.fullmatch(str(key))
                context = inherited
                if heading:
                    context = (
                        "preferred"
                        if (heading[1] or "").lower() in {"preferred", "desired"}
                        else "required"
                    )
                yield from _leaves(part, source + "." + str(key), context)
    elif isinstance(value, list):
        # An explicit structured enum of degree names represents alternatives;
        # full qualification sentences in a list remain independent obligations.
        if value and all(
            isinstance(part, str) and _CREDENTIAL.fullmatch(part.strip()) for part in value
        ):
            yield source, "/".join(value), inherited
        else:
            for index, part in enumerate(value):
                yield from _leaves(part, f"{source}[{index}]", inherited)
    elif isinstance(value, str):
        yield source, evidence_text(value), inherited


def qualifications(value: object, source: str, default: str = "unknown") -> list[Qualification]:
    result = []
    for path, text, inherited in _leaves(value, source, default):
        # Sentence punctuation must not split dotted degree abbreviations.
        for sentence in _sentences(text):
            sentence = sentence.strip().rstrip(".!?")
            if not sentence:
                continue
            source_clause = sentence
            heading = _HEADING.fullmatch(sentence)
            if heading:
                inherited = (
                    "preferred"
                    if (heading[1] or "").lower() in {"preferred", "desired"}
                    else "required"
                )
                continue
            # Inline heading applies to this clause, not the rest of another field.
            prefix, colon, rest = sentence.partition(":")
            heading = _HEADING.fullmatch(prefix) if colon else None
            context = inherited
            if heading:
                context = (
                    "preferred"
                    if (heading[1] or "").lower() in {"preferred", "desired"}
                    else "required"
                )
                inherited = context
                sentence = rest.strip()
            if re.search(r"\b(?:must|requires?)\b", _fragments(sentence)[0], re.I):
                context = "required"
            # Conjoined credentials share a trailing modality, but are not
            # alternatives. Do not mistake this for two unrelated subjects.
            degree_matches = _matches(sentence)
            for left, right in reversed(list(zip(degree_matches, degree_matches[1:]))):
                link = sentence[left.end() : right.start()]
                if re.fullmatch(r"\s+and\s+", link, re.I):
                    sentence = sentence[: left.end()] + " & " + sentence[right.start() :]
            sentence = re.sub(
                r"\b(required|preferred|desired|optional)\s*,\s*(?!but\b)|"
                r",\s*(?=(?:experience\s+)?(?:work(?:ing)?|collaborat(?:e|ing))\s+with\b)",
                lambda match: (match[1] or "") + "; ",
                sentence,
                flags=re.I,
            )
            fragments = [part for chunk in sentence.split(";") for part in _fragments(chunk)]
            reference_uncertain = any(
                not _matches(part)
                and re.match(
                    r"\s*,?\s*(?:is\s+)?(?:(?:required|preferred)(?:\s+(?:for|depending|in|on|when)\b|\s*$)|(?:may|might)\s+be\b)",
                    part,
                    re.I,
                )
                for part in fragments
            )
            for fragment in fragments:
                fragment = fragment.strip(" ,")
                if not fragment:
                    continue
                matches = _matches(fragment)
                credentials = tuple(_credential(match[0]) for match in matches)
                links = [
                    fragment[left.end() : right.start()]
                    for left, right in zip(matches, matches[1:])
                ]
                alternatives = (
                    len(matches) > 1
                    and all(_alternative_link(link) for link in links)
                    and any(re.search(r"/|\bor\b", link, re.I) for link in links)
                )
                modality = _modality(fragment, context)
                uncertain = (
                    reference_uncertain
                    or bool(_UNCERTAIN.search(fragment))
                    or bool(
                        _PREFERRED.search(fragment)
                        and re.search(r"\b(?:must|required|requires?|only)\b", fragment, re.I)
                    )
                )
                result.append(
                    Qualification(
                        path,
                        fragment,
                        credentials,
                        modality,
                        alternatives,
                        uncertain,
                        source_clause,
                        fragment if not credentials else None,
                    )
                )
    return result


def degree_outcome(evidence: list[Qualification]) -> str:
    outcomes = []
    for item in evidence:
        if "PhD" not in item.credentials:
            continue
        if item.uncertain:
            outcomes.append("review")
        elif item.modality in {"preferred", "optional", "mentioned"}:
            continue
        elif item.alternatives and any(degree in {"BS", "MS"} for degree in item.credentials):
            continue
        elif item.modality == "required":
            outcomes.append("reject")
        else:
            outcomes.append("review")
    return "reject" if "reject" in outcomes else "review" if outcomes else "accept"
