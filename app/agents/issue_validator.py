import re
from typing import Any


PRIORITIES = {"Highest", "High", "Medium", "Low", "Lowest"}
SUPPORTED_ISSUE_TYPES = {"Epic", "Story", "Task", "Bug", "Sub-task"}

# Keep these templates explicit so teams can adjust them to their Jira process.
ISSUE_FORMAT_RULES = {
    "Task": {
        "Goal": ("Objective",),
        "Acceptance Criteria": ("Done When",),
        "Definition of Ready": ("DoR",),
        "Definition of Done": ("DoD",),
    },
    "Bug": {
        "Steps to Reproduce": ("Reproduction Steps",),
        "Expected Result": ("Expected Behavior", "Expected Behaviour"),
        "Actual Result": ("Actual Behavior", "Actual Behaviour"),
        "Impact": (),
        "Definition of Ready": ("DoR",),
        "Definition of Done": ("DoD",),
    },
}

_PROJECT_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_PLACEHOLDERS = {"", "tbd", "todo", "n/a", "not provided", "unknown"}


def _normalise_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _parse_sections(description: str, template: dict[str, tuple[str, ...]]) -> dict[str, str]:
    labels = {}
    for canonical, aliases in template.items():
        for label in (canonical, *aliases):
            labels[_normalise_heading(label)] = canonical

    sections: dict[str, list[str]] = {}
    active = None
    for line in description.splitlines():
        candidate = line.strip()
        candidate = re.sub(r"^#{1,6}\s*", "", candidate)
        candidate = candidate.strip("* `")
        heading, separator, remainder = candidate.partition(":")
        canonical = labels.get(_normalise_heading(heading))
        if canonical:
            active = canonical
            sections.setdefault(active, [])
            if separator and remainder.strip():
                sections[active].append(remainder.strip())
        elif active:
            sections[active].append(line.strip())

    return {name: "\n".join(parts).strip() for name, parts in sections.items()}


def _error(field: str, problem: str, text: str, suggestion: str) -> dict[str, str]:
    return {
        "field": field,
        "problem": problem,
        "text": text[:300],
        "suggestion": suggestion,
    }


def _is_placeholder(section: str) -> bool:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if not lines:
        return True
    normalized = []
    for line in lines:
        line = re.sub(r"^[-*]\s*(?:\[[ xX]\]\s*)?", "", line)
        normalized.append(_normalise_heading(line))
    return all(line in _PLACEHOLDERS for line in normalized)


def validate_jira_issue(arguments: dict[str, Any]) -> list[dict[str, str]]:
    """Return blocking, field-specific issues before a Jira create call."""
    errors = []
    issue_type = arguments.get("issue_type")
    if issue_type not in SUPPORTED_ISSUE_TYPES:
        errors.append(_error(
            "issue_type",
            "This Jira issue type is not supported by the agent.",
            str(issue_type or ""),
            "Choose Epic, Story, Task, Bug, or Sub-task.",
        ))
        return errors

    project_key = arguments.get("project_key")
    if not isinstance(project_key, str) or not _PROJECT_KEY.fullmatch(project_key):
        errors.append(_error(
            "project_key", "This does not look like a valid Jira project key.",
            str(project_key or ""), "Provide the project key, for example AD.",
        ))

    summary = arguments.get("summary")
    if not isinstance(summary, str) or not 8 <= len(summary.strip()) <= 120:
        errors.append(_error(
            "summary", "Summary must be between 8 and 120 characters.",
            str(summary or ""), "Use a concise summary describing the task or bug.",
        ))

    priority = arguments.get("priority")
    if priority not in PRIORITIES:
        errors.append(_error(
            "priority", "Priority is not supported.", str(priority or ""),
            "Choose Highest, High, Medium, Low, or Lowest.",
        ))

    description = arguments.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(_error(
            "description", "Description is required.", str(description or ""),
            "Fill in the required sections for this issue type.",
        ))
        return errors

    parent_key = arguments.get("parent_key")
    if issue_type == "Sub-task" and not isinstance(parent_key, str):
        errors.append(_error(
            "parent_key", "A Sub-task must have a parent issue.", "[missing]",
            "Provide the parent issue key, such as AD-12.",
        ))

    # Task and Bug use the team's detailed templates. Epic, Story, and Sub-task
    # accept a normal description; their available fields can vary by project.
    if issue_type not in ISSUE_FORMAT_RULES:
        return errors

    template = ISSUE_FORMAT_RULES[issue_type]
    sections = _parse_sections(description, template)
    for required, aliases in template.items():
        section = sections.get(required)
        field = f"description.{required.lower().replace(' ', '_')}"
        if section is None:
            labels = ", ".join((required, *aliases))
            errors.append(_error(
                field, f"Required section '{required}' is missing.", "[missing]",
                f"Add a '{required}:' section (accepted headings: {labels}).",
            ))
        elif _is_placeholder(section):
            errors.append(_error(
                field, f"Required section '{required}' has no usable content.", section,
                f"Replace the placeholder with actual {required.lower()} details.",
            ))

    return errors
