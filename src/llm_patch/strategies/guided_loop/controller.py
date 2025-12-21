"""Guided Convergence Loop orchestration scaffolding."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from textwrap import dedent
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Match, Optional, Protocol, Sequence, Tuple

from diff_match_patch import diff_match_patch

from llm_patch.patch_applier import PatchApplier, normalize_replacement_block
PATCH_CONSTRAINTS_TEXT = "\n".join(
    [
        "- Do not reformat unrelated code.",
        "- Do not rename symbols.",
        "- Change only within this method unless strictly necessary.",
        "- Prefer the smallest valid replacement and include only the lines that must change.",
    ]
)

PATCH_EXAMPLE_DIFF = (
    "ORIGINAL LINES:\n"
    "return tokens.stream()\n"
    "        .map(token -> token.equals(\"-\") && inPrefixContext(previous))\n"
    "                ? \"0-\" : token);\n"
    "CHANGED LINES:\n"
    "return tokens.stream()\n"
    "        .map(token -> token.equals(\"-\") && inPrefixContext(previous)\n"
    "                ? \"0-\" : token)\n"
    "        .collect(Collectors.toList());\n"
)

REPLACEMENT_BLOCK_PATTERN = re.compile(
    r"ORIGINAL LINES:\s*\n(?P<original>.*?)\n(?:CHANGED|NEW) LINES:\s*\n(?P<updated>.*?)(?=(?:\nORIGINAL LINES:|\Z))",
    re.DOTALL,
)

from ..base import PatchRequest, PatchResult, PatchStrategy, StrategyEvent, StrategyEventKind
from .phases import (
    GuidedIterationArtifact,
    GuidedLoopTrace,
    GuidedPhase,
    PhaseArtifact,
    PhaseStatus,
)
from .prompt_fragments import (
    CONSTRAINTS_FRAGMENT,
    CONTEXT_FRAGMENT,
    CRITIQUE_FRAGMENT,
    CRITIQUE_OUTPUT_FRAGMENT,
    DIAGNOSE_INSTRUCTIONS_FRAGMENT,
    DIAGNOSIS_RATIONALE_FRAGMENT,
    DIAGNOSIS_OUTPUT_FRAGMENT,
    DIAGNOSIS_SUMMARY_FRAGMENT,
    ERROR_FRAGMENT,
    EXAMPLE_REPLACEMENT_FRAGMENT,
    EXPERIMENT_INSTRUCTIONS_FRAGMENT,
    EXPERIMENT_SUMMARY_FRAGMENT,
    GATHERED_CONTEXT_FRAGMENT,
    GATHER_INSTRUCTIONS_FRAGMENT,
    GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
    HISTORY_FRAGMENT,
    PATCH_DIAGNOSTICS_FRAGMENT,
    PRIOR_PATCH_FRAGMENT,
    PREVIOUS_DIFF_FRAGMENT,
    PROPOSE_INSTRUCTIONS_FRAGMENT,
    REFINEMENT_CONTEXT_FRAGMENT,
    PROPOSAL_SUMMARY_FRAGMENT,
    compose_prompt,
)


class LLMClient(Protocol):
    """Minimal client interface that the controller depends on."""

    def complete(self, *, prompt: str, temperature: float, model: Optional[str] = None) -> str:  # pragma: no cover - protocol
        """Return a text completion for ``prompt``."""


@dataclass(slots=True)
class GuidedLoopConfig:
    """Runtime configuration for the guided loop strategy."""

    max_iterations: int = 1
    refine_sub_iterations: int = 3
    main_loop_passes: int = 2
    interpreter_model: str = "planner"
    patch_model: str = "patcher"
    critique_model: Optional[str] = None
    temperature: float = 0.0
    auto_constraints: bool = True
    compile_check: bool = True

    def total_iterations(self) -> int:
        base = max(1, self.max_iterations)
        refinements = max(0, self.refine_sub_iterations)
        passes = max(1, self.main_loop_passes)
        return (base + refinements) * passes

@dataclass(slots=True)
class GuidedLoopInputs(PatchRequest):
    """Adds guided-loop specific context to the base patch request."""

    compile_command: Optional[Sequence[str]] = None
    additional_context: Mapping[str, Any] = field(default_factory=dict)
    history_seed: Sequence[str] = field(default_factory=tuple)
    initial_outcome: Optional[Mapping[str, Any]] = None
    raw_error_text: Optional[str] = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial wiring
        if self.raw_error_text is None:
            self.raw_error_text = self.error_text


@dataclass(slots=True)
class GuidedLoopResult(PatchResult):
    """Extends the base ``PatchResult`` with a structured trace."""

    trace: GuidedLoopTrace | None = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None
    patch_diagnostics: Optional[str] = None


@dataclass(slots=True)
class IterationOutcome:
    """Container for deterministic critique + compile results."""

    diff_text: Optional[str] = None
    patched_text: Optional[str] = None
    patch_applied: bool = False
    patch_diagnostics: Optional[str] = None
    compile_returncode: Optional[int] = None
    compile_stdout: Optional[str] = None
    compile_stderr: Optional[str] = None
    critique_feedback: Optional[str] = None
    hypothesis_id: Optional[str] = None
    error_fingerprint: Optional[str] = None
    previous_error_fingerprint: Optional[str] = None
    diff_span: Optional[Tuple[int, int]] = None
    error_message: Optional[str] = None
    error_location: Optional[int] = None

    @property
    def compile_success(self) -> bool:
        return self.compile_returncode == 0 if self.compile_returncode is not None else False


class GuidedConvergenceStrategy(PatchStrategy):
    """High-level orchestration of the Guided Convergence Loop."""

    name = "guided-loop"

    PROMPT_TEMPLATES: Mapping[GuidedPhase, str] = {
        GuidedPhase.DIAGNOSE: compose_prompt(
            DIAGNOSE_INSTRUCTIONS_FRAGMENT,
            HISTORY_FRAGMENT,
            PRIOR_PATCH_FRAGMENT,
            CRITIQUE_FRAGMENT,
            ERROR_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.PLANNING: compose_prompt(
            EXPERIMENT_INSTRUCTIONS_FRAGMENT,
            DIAGNOSIS_OUTPUT_FRAGMENT,
            CRITIQUE_OUTPUT_FRAGMENT,
        ),
        GuidedPhase.GATHER: compose_prompt(
            GATHER_INSTRUCTIONS_FRAGMENT,
            ERROR_FRAGMENT,
            EXPERIMENT_SUMMARY_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.PROPOSE: compose_prompt(
            PROPOSE_INSTRUCTIONS_FRAGMENT,
            REFINEMENT_CONTEXT_FRAGMENT,
            ERROR_FRAGMENT,
            EXPERIMENT_SUMMARY_FRAGMENT,
            GATHERED_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
        ),
        GuidedPhase.GENERATE_PATCH: compose_prompt(
            GENERATE_PATCH_INSTRUCTIONS_FRAGMENT,
            PROPOSAL_SUMMARY_FRAGMENT,
            ERROR_FRAGMENT,
            DIAGNOSIS_SUMMARY_FRAGMENT,
            DIAGNOSIS_RATIONALE_FRAGMENT,
            GATHERED_CONTEXT_FRAGMENT,
            CONTEXT_FRAGMENT,
            CONSTRAINTS_FRAGMENT,
            EXAMPLE_REPLACEMENT_FRAGMENT,
        ),
        GuidedPhase.CRITIQUE: dedent(
            """
            Begin with a Markdown heading that states the hypothesis label and its description (for example: "### H2 – Missing comma in enum").
            Critique the replacement block(s). Do they respect the constraints? Identify non-minimal or risky edits.
            Tie your observations back to the named hypothesis so later phases can cite this critique verbatim.
            """
        ),
    }

    POINTER_SUMMARY_LANGUAGES = {"java", "c"}
    ERROR_LINE_PATTERN = re.compile(r"\berror\s*:", re.IGNORECASE)
    WARNING_LINE_PATTERN = re.compile(r"\bwarning\s*:", re.IGNORECASE)
    NOTE_LINE_PATTERN = re.compile(r"\bnote\s*:", re.IGNORECASE)
    POINTER_ALLOWED_CHARS = frozenset({"^", "~", "|", "│"})
    TOKEN_PATTERN = re.compile(r"\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|\w+|[^\s\w]", re.UNICODE)
    CONTEXT_RADIUS = 5
    SUFFIX_COLLAPSE_MAX_LINES = 8
    SUFFIX_COLLAPSE_SIMILARITY = 0.97
    GATHER_ALLOWED_CATEGORIES = {
        "ENCLOSING_SCOPE",
        "DECLARATION",
        "IMPORTS_NAMESPACE",
        "TYPE_CONTEXT",
        "FILE_CONTEXT",
        "USAGE_CONTEXT",
    }
    GATHER_ALLOWED_TARGET_KINDS = {"symbol", "type", "module", "unknown"}

    def __init__(
        self,
        client: LLMClient | None = None,
        config: GuidedLoopConfig | None = None,
        observer=None,
    ) -> None:
        super().__init__(observer)
        self._client = client
        self._config = config or GuidedLoopConfig()
        self._patch_applier = PatchApplier()
        self._dmp = diff_match_patch()
        self._baseline_error_fingerprint: Optional[str] = None
        self._latest_diagnosis_output: Optional[str] = None
        self._critique_transcripts: list[str] = []

    def run(self, request: PatchRequest) -> GuidedLoopResult:
        inputs = self._ensure_inputs(request)
        self._latest_diagnosis_output = None
        self._critique_transcripts = []
        baseline_source = inputs.raw_error_text or inputs.error_text
        self._baseline_error_fingerprint = self._error_fingerprint(baseline_source)
        trace = self._plan_trace(inputs)
        planning_event = self._event(
            kind=StrategyEventKind.NOTE,
            message="Guided loop plan generated",
            data={"iterations": len(trace.iterations), "mode": "guided-loop"},
        )
        self.emit(planning_event)
        events: List[StrategyEvent] = [planning_event]
        history_log = self._initial_history(inputs)
        prior_outcome = self._seed_prior_outcome(inputs)
        iteration_outcome: IterationOutcome | None = prior_outcome
        for iteration in trace.iterations:
            history_context = self._format_history(history_log)
            iteration.history_context = history_context
            iteration_events, iteration_outcome = self._execute_iteration(
                iteration,
                inputs,
                prior_outcome=prior_outcome,
                history_context=history_context,
            )
            events.extend(iteration_events)
            if iteration_outcome:
                history_entry = self._history_entry(iteration.index, iteration_outcome)
                iteration.history_entry = history_entry
                history_log.append(history_entry)
                post_iteration_events = self._post_iteration_evaluation(iteration, iteration_outcome, prior_outcome)
                events.extend(post_iteration_events)
            prior_outcome = iteration_outcome
            if iteration_outcome and iteration_outcome.patch_applied and (
                not self._config.compile_check
                or not inputs.compile_command
                or iteration_outcome.compile_success
            ):
                break
        applied = iteration_outcome.patch_applied if iteration_outcome else False
        success = iteration_outcome.compile_success if iteration_outcome else False
        after_text = iteration_outcome.patched_text if iteration_outcome and iteration_outcome.patch_applied else None
        diff_text = iteration_outcome.diff_text if iteration_outcome else None
        compile_returncode = iteration_outcome.compile_returncode if iteration_outcome else None
        compile_stdout = iteration_outcome.compile_stdout if iteration_outcome else None
        compile_stderr = iteration_outcome.compile_stderr if iteration_outcome else None
        patch_diagnostics = iteration_outcome.patch_diagnostics if iteration_outcome else None
        notes = self._result_notes(iteration_outcome)
        return GuidedLoopResult(
            applied=applied,
            success=success,
            after_text=after_text,
            diff_text=diff_text,
            notes=notes,
            events=events,
            artifacts=[iteration.to_dict() for iteration in trace.iterations],
            trace=trace,
            compile_returncode=compile_returncode,
            compile_stdout=compile_stdout,
            compile_stderr=compile_stderr,
            patch_diagnostics=patch_diagnostics,
        )

    # ------------------------------------------------------------------
    def _ensure_inputs(self, request: PatchRequest) -> GuidedLoopInputs:
        if isinstance(request, GuidedLoopInputs):
            processed_error = self._prepare_compile_error_text(
                request.raw_error_text or request.error_text,
                request.language,
            )
            request.error_text = processed_error
            return request
        extra_context: Mapping[str, Any] = dict(request.extra or {})
        history_seed_value = extra_context.get("history_seed", [])
        if isinstance(history_seed_value, str):
            history_seed: Sequence[str] = (history_seed_value,)
        elif isinstance(history_seed_value, Sequence):
            history_seed = tuple(str(item) for item in history_seed_value)
        else:
            history_seed = tuple()
        initial_outcome_value = extra_context.get("initial_outcome")
        initial_outcome = initial_outcome_value if isinstance(initial_outcome_value, Mapping) else None
        processed_error = self._prepare_compile_error_text(request.error_text, request.language)
        return GuidedLoopInputs(
            case_id=request.case_id,
            language=request.language,
            source_path=request.source_path,
            source_text=request.source_text,
            error_text=processed_error,
            manifest=request.manifest,
            extra=request.extra,
            raw_error_text=request.error_text,
            additional_context=extra_context,
            history_seed=history_seed,
            initial_outcome=initial_outcome,
        )

    def _prepare_compile_error_text(self, error_text: Optional[str], language: Optional[str]) -> str:
        raw_text = error_text or ""
        text = raw_text.strip()
        if not text:
            return ""
        language_key = (language or "").lower()
        if language_key not in self.POINTER_SUMMARY_LANGUAGES:
            return raw_text
        block = self._extract_first_error_block(text)
        lines = block.splitlines() if block else text.splitlines()
        pointer_summary = self._pointer_summary(lines, language_key)
        cleaned_lines = self._trim_trailing_blanks(lines)
        if pointer_summary:
            cleaned_lines = cleaned_lines + ["", pointer_summary]
        return "\n".join(cleaned_lines).strip()

    def _extract_first_error_block(self, error_text: str) -> str:
        lines = error_text.splitlines()
        start_idx = None
        for idx, line in enumerate(lines):
            if self.ERROR_LINE_PATTERN.search(line):
                start_idx = idx
                break
        if start_idx is None:
            return error_text.strip()
        end_idx = self._error_block_end_index(lines, start_idx)
        prefix_lines: list[str] = []
        prefix_idx = start_idx - 1
        while prefix_idx >= 0 and len(prefix_lines) < 3:
            candidate = lines[prefix_idx].strip()
            if not candidate:
                break
            if candidate.endswith(":") or candidate.lower().startswith("in "):
                prefix_lines.insert(0, lines[prefix_idx])
                prefix_idx -= 1
                continue
            break
        block_lines = prefix_lines + lines[start_idx:end_idx]
        trimmed = self._trim_trailing_blanks(block_lines)
        cleaned = self._strip_trailing_context_headers(trimmed)
        return "\n".join(cleaned).strip()

    def _error_block_end_index(self, lines: Sequence[str], start_idx: int) -> int:
        pointer_relative_idx = self._find_pointer_line(lines[start_idx:])
        if pointer_relative_idx is not None:
            return start_idx + pointer_relative_idx + 1
        for idx in range(start_idx + 1, len(lines)):
            line = lines[idx]
            if self.ERROR_LINE_PATTERN.search(line) or self._is_warning_or_note_line(line):
                return idx
        return len(lines)

    @staticmethod
    def _trim_trailing_blanks(lines: Sequence[str]) -> list[str]:
        trimmed = list(lines)
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        while trimmed and not trimmed[0].strip():
            trimmed.pop(0)
        return trimmed

    def _strip_trailing_context_headers(self, lines: Sequence[str]) -> list[str]:
        cleaned = list(lines)
        while cleaned and cleaned[-1].strip().endswith(":") and "error" not in cleaned[-1].lower():
            cleaned.pop()
        return cleaned

    def _is_warning_or_note_line(self, line: str) -> bool:
        return bool(self.WARNING_LINE_PATTERN.search(line) or self.NOTE_LINE_PATTERN.search(line))

    def _pointer_summary(self, lines: Sequence[str], language: Optional[str]) -> Optional[str]:
        if not language or language.lower() not in self.POINTER_SUMMARY_LANGUAGES:
            return None
        pointer_index = self._find_pointer_line(lines)
        if pointer_index is None or pointer_index == 0:
            return None
        code_line = lines[pointer_index - 1]
        pointer_line = lines[pointer_index]
        return self._describe_pointer_context(code_line, pointer_line)

    def _find_pointer_line(self, lines: Sequence[str]) -> Optional[int]:
        allowed = self.POINTER_ALLOWED_CHARS
        for idx, line in enumerate(lines):
            if "^" not in line:
                continue
            normalized = line.replace("│", "|")
            stripped = normalized.strip()
            if not stripped:
                continue
            filtered = "".join(ch for ch in stripped if not ch.isspace())
            remainder = "".join(ch for ch in filtered if ch not in allowed)
            if not remainder:
                return idx
        return None

    def _describe_pointer_context(self, code_line: str, pointer_line: str) -> Optional[str]:
        pointer_expanded = pointer_line.expandtabs(4)
        caret_index = pointer_expanded.find("^")
        if caret_index == -1:
            return None
        code_expanded = code_line.expandtabs(4)
        context = self._token_context_descriptions(code_expanded, caret_index)
        prev_desc = context["previous"]
        current_desc = context["current"]
        summary = f"Position of error on line - previous token: {prev_desc}; current token: {current_desc}."
        marked_line = self._line_with_marker(code_line, caret_index)
        if not marked_line:
            return summary
        snippet_lines = [
            summary,
            "In the following snippet, the position of the error is denoted by  <ERROR> ",
            marked_line,
        ]
        return "\n".join(snippet_lines)

    def _line_with_marker(self, code_line: str, caret_index: int, marker: str = " <ERROR> ") -> str:
        tab_size = 4
        column = 0
        for idx, char in enumerate(code_line):
            if char == "\t":
                remainder = column % tab_size
                step = tab_size - remainder if remainder else tab_size
            else:
                step = 1
            if caret_index < column + step:
                return f"{code_line[:idx]}{marker}{code_line[idx:]}"
            column += step
        return f"{code_line}{marker}"

    def _token_context_descriptions(self, code_line: str, caret_index: int) -> Mapping[str, str]:
        tokens = list(self.TOKEN_PATTERN.finditer(code_line))
        prev_match = None
        current_match = None
        next_match = None
        for match in tokens:
            start, end = match.span()
            if end <= caret_index:
                prev_match = match
                continue
            if start <= caret_index < end:
                current_match = match
                continue
            if start > caret_index:
                next_match = match
                break
        current_desc = self._describe_token(current_match, default="a whitespace column")
        prev_desc = self._describe_token(prev_match, default="start of line")
        next_desc = self._describe_token(next_match, default="end of line")
        return {"current": current_desc, "previous": prev_desc, "next": next_desc}

    @staticmethod
    def _describe_token(match: Match[str] | None, *, default: str) -> str:
        if match is None:
            return default
        token = match.group()
        if not token:
            return default
        if token.isidentifier():
            return f"identifier {token!r}"
        if token.replace("_", "").isdigit():
            return f"number {token!r}"
        if token.startswith(("\"", "'")):
            return f"literal {token}"
        return f"symbol {token!r}"

    @staticmethod
    def _symbol_label(symbol: Optional[str], *, default: str) -> str:
        if symbol is None:
            return default
        if symbol == " ":
            return "a space"
        if symbol == "\t":
            return "a tab"
        if symbol == "\n":
            return "a newline"
        if symbol.isprintable():
            return repr(symbol)
        return f"U+{ord(symbol):04X}"

    def _seed_prior_outcome(self, inputs: GuidedLoopInputs) -> IterationOutcome | None:
        payload = inputs.initial_outcome or inputs.additional_context.get("initial_outcome")
        if not payload or not isinstance(payload, Mapping):
            return None
        return IterationOutcome(
            diff_text=payload.get("diff_text"),
            patched_text=payload.get("patched_text"),
            patch_applied=bool(payload.get("patch_applied", False)),
            patch_diagnostics=payload.get("patch_diagnostics"),
            compile_returncode=payload.get("compile_returncode"),
            compile_stdout=payload.get("compile_stdout"),
            compile_stderr=payload.get("compile_stderr"),
            critique_feedback=payload.get("critique_feedback"),
        )

    def _initial_history(self, inputs: GuidedLoopInputs) -> List[str]:
        entries: List[str] = []
        entries.extend(self._coerce_history_entries(inputs.history_seed))
        entries.extend(self._coerce_history_entries(inputs.additional_context.get("history_seed")))
        return entries

    def _format_history(self, entries: Sequence[str], limit: int = 5) -> str:
        filtered = [entry for entry in entries if entry]
        if not filtered:
            return self._history_placeholder()
        tail = filtered[-limit:]
        return "\n".join(f"- {entry}" for entry in tail)

    def _history_entry(self, iteration_index: int, outcome: IterationOutcome) -> str:
        patch_state = "applied" if outcome.patch_applied else "not applied"
        if outcome.patch_applied:
            if outcome.compile_returncode is None:
                compile_desc = "compile/test skipped"
            elif outcome.compile_success:
                compile_desc = "compile/test passed"
            else:
                compile_desc = f"compile/test failed (rc={outcome.compile_returncode})"
        else:
            compile_desc = outcome.patch_diagnostics or "patch unavailable"
        critique_line = ""
        if outcome.critique_feedback:
            head = outcome.critique_feedback.strip().splitlines()[0].strip()
            if head:
                critique_line = f"critique: {head}"
        parts = [f"Loop {iteration_index}: patch {patch_state}", compile_desc]
        if critique_line:
            parts.append(critique_line)
        return "; ".join(parts)

    @staticmethod
    def _coerce_history_entries(source: Any) -> List[str]:
        if not source:
            return []
        if isinstance(source, str):
            text = source.strip()
            return [text] if text else []
        if isinstance(source, Sequence):
            entries: List[str] = []
            for item in source:
                if item is None:
                    continue
                text = str(item).strip()
                if text:
                    entries.append(text)
            return entries
        text = str(source).strip()
        return [text] if text else []

    def _plan_trace(self, request: GuidedLoopInputs) -> GuidedLoopTrace:
        trace = GuidedLoopTrace(
            strategy=self.name,
            target_language=request.language,
            case_id=request.case_id,
            build_command=" ".join(request.compile_command or []) or None,
        )
        primary_iterations = max(1, self._config.max_iterations)
        refine_iterations = max(0, self._config.refine_sub_iterations)
        passes = max(1, self._config.main_loop_passes)
        iteration_counter = 0
        loop_counter = 0
        refine_counter = 0

        for pass_index in range(1, passes + 1):
            include_full_critiques = pass_index > 1
            for _ in range(primary_iterations):
                iteration_counter += 1
                loop_counter += 1
                label = f"Loop {loop_counter}"
                iteration = GuidedIterationArtifact(
                    index=iteration_counter,
                    kind="primary",
                    label=label,
                    pass_index=pass_index,
                    include_full_critiques=include_full_critiques,
                )
                for phase in self._phase_order(kind="primary"):
                    prompt = self._render_prompt(phase, request)
                    artifact = PhaseArtifact(phase=phase, status=PhaseStatus.PLANNED, prompt=prompt)
                    trace.add_phase(iteration, artifact)
                trace.iterations.append(iteration)

            for _ in range(refine_iterations):
                iteration_counter += 1
                refine_counter += 1
                label = f"Refine {refine_counter}"
                iteration = GuidedIterationArtifact(
                    index=iteration_counter,
                    kind="refine",
                    label=label,
                    pass_index=pass_index,
                    include_full_critiques=include_full_critiques,
                )
                for phase in self._phase_order(kind="refine"):
                    prompt = self._render_prompt(phase, request)
                    artifact = PhaseArtifact(phase=phase, status=PhaseStatus.PLANNED, prompt=prompt)
                    trace.add_phase(iteration, artifact)
                trace.iterations.append(iteration)
        trace.notes = (
            "Trace contains prompt templates only. Actual execution will attach responses, checks, "
            "and iteration history entries for each loop."
        )
        return trace

    def _phase_order(self, *, kind: str = "primary") -> List[GuidedPhase]:
        if kind == "refine":
            return [
                GuidedPhase.PLANNING,
                GuidedPhase.GATHER,
                GuidedPhase.PROPOSE,
                GuidedPhase.GENERATE_PATCH,
                GuidedPhase.CRITIQUE,
            ]
        return [
            GuidedPhase.DIAGNOSE,
            GuidedPhase.PLANNING,
            GuidedPhase.GATHER,
            GuidedPhase.PROPOSE,
            GuidedPhase.GENERATE_PATCH,
            GuidedPhase.CRITIQUE,
        ]

    def _render_prompt(
        self,
        phase: GuidedPhase,
        request: GuidedLoopInputs,
        *,
        context_override: Optional[str] = None,
        extra: Optional[Mapping[str, str]] = None,
    ) -> str:
        template = self.PROMPT_TEMPLATES[phase]
        filename = request.source_path.name
        context = context_override if context_override is not None else self._context_for_phase(phase, request)
        data: Dict[str, str] = {
            "language": request.language,
            "error": request.error_text or "(error unavailable)",
            "context": context,
            "filename": filename,
            "diagnosis": self._diagnosis_placeholder(),
            "diagnosis_explanation": self._diagnosis_explanation_placeholder(),
            "proposal": self._proposal_placeholder(),
            "constraints": PATCH_CONSTRAINTS_TEXT,
            "example_diff": PATCH_EXAMPLE_DIFF,
            "critique_feedback": self._critique_placeholder(),
            "previous_diff": self._previous_diff_placeholder(),
            "patch_diagnostics": "",
            "history_context": self._history_placeholder(),
            "prior_patch_summary": self._prior_patch_placeholder(),
            "refinement_context": self._refinement_context_placeholder(),
            "diagnosis_output": self._diagnosis_output_placeholder(),
            "experiment_summary": self._experiment_summary_placeholder(),
            "critique_output": self._critique_output_placeholder(),
            "gathered_context": self._gathered_context_placeholder(),
        }
        if extra:
            data.update({key: value for key, value in extra.items() if value is not None})
        populated = template.format(**data)
        return self._strip_placeholder_sections(populated)

    @classmethod
    def _placeholder_texts(cls) -> set[str]:
        return {
            cls._history_placeholder(),
            cls._critique_placeholder(),
            cls._previous_diff_placeholder(),
            cls._diagnosis_placeholder(),
            cls._diagnosis_explanation_placeholder(),
            cls._proposal_placeholder(),
            cls._patch_diagnostics_placeholder(),
            cls._prior_patch_placeholder(),
            cls._refinement_context_placeholder(),
            cls._diagnosis_output_placeholder(),
            cls._experiment_summary_placeholder(),
            cls._critique_output_placeholder(),
            cls._gathered_context_placeholder(),
        }

    def _strip_placeholder_sections(self, text: str) -> str:
        placeholder_texts = self._placeholder_texts()
        lines = text.splitlines()
        cleaned: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.rstrip().endswith(":") and i + 1 < len(lines):
                placeholder_candidate = lines[i + 1].strip()
                if placeholder_candidate in placeholder_texts:
                    i += 2
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    continue
            cleaned.append(line)
            i += 1
        # collapse excessive blank lines
        collapsed: list[str] = []
        previous_blank = True
        for line in cleaned:
            if line.strip():
                collapsed.append(line)
                previous_blank = False
            else:
                if not previous_blank:
                    collapsed.append("")
                previous_blank = True
        return "\n".join(collapsed).strip()

    # ------------------------------------------------------------------
    def _execute_iteration(
        self,
        iteration: GuidedIterationArtifact,
        request: GuidedLoopInputs,
        *,
        prior_outcome: IterationOutcome | None,
        history_context: str,
    ) -> tuple[List[StrategyEvent], IterationOutcome | None]:
        events: List[StrategyEvent] = []
        if iteration.kind == "refine":
            reset_events = self._reset_for_refinement(iteration)
            for event in reset_events:
                self.emit(event)
            events.extend(reset_events)
        outcome: IterationOutcome | None = None
        continue_execution = True
        previous_error_fingerprint = prior_outcome.error_fingerprint if prior_outcome else self._baseline_error_fingerprint
        for artifact in iteration.phases:
            if not continue_execution:
                break
            if artifact.status == PhaseStatus.PLANNED:
                self._prepare_phase_prompt(
                    artifact,
                    iteration,
                    request,
                    prior_outcome=prior_outcome,
                    history_context=history_context,
                )
            if artifact.phase == GuidedPhase.DIAGNOSE:
                if continue_execution:
                    events.extend(self._execute_diagnose(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.PLANNING:
                if continue_execution:
                    events.extend(self._execute_planning(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.GATHER:
                if continue_execution:
                    events.extend(self._execute_gather(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.PROPOSE:
                if continue_execution:
                    events.extend(self._execute_propose(artifact, iteration, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.GENERATE_PATCH:
                if continue_execution:
                    events.extend(self._execute_generate_patch(artifact, iteration.index, request))
                    continue_execution = artifact.status == PhaseStatus.COMPLETED
            elif artifact.phase == GuidedPhase.CRITIQUE:
                if continue_execution:
                    critique_events, outcome = self._execute_critique(artifact, iteration, iteration.index, request)
                    events.extend(critique_events)
                break
            else:
                break
        if outcome:
            outcome.previous_error_fingerprint = previous_error_fingerprint
        return events, outcome

    def _reset_for_refinement(self, iteration: GuidedIterationArtifact) -> List[StrategyEvent]:
        event = self._event(
            kind=StrategyEventKind.NOTE,
            message="Refinement iteration skipping Diagnose; reusing most recent analysis",
            iteration=iteration.index,
        )
        return [event]

    def _execute_diagnose(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Diagnose phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Diagnose phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Diagnose phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        if artifact.response:
            self._latest_diagnosis_output = artifact.response
        if not artifact.response:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Diagnose phase returned an empty response."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Diagnose phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["diagnosis_text"] = artifact.response
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Diagnose phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_planning(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Planning phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.interpreter_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Planning phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Planning phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events

        artifact.response = response.strip()
        if not artifact.response:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Planning phase returned an empty response."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Planning phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            iteration.failure_reason = "empty-response"
            self.emit(failure_event)
            events.append(failure_event)
            return events

        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["planning_notes"] = artifact.response
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Planning phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_gather(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Gather phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)

        base_prompt = artifact.prompt
        response_text: str = ""
        parsed: Optional[Dict[str, Any]] = None
        last_error: Optional[str] = None
        attempts = 0
        for attempt in range(1, 4):
            attempts = attempt
            try:
                # Gather requires strict structured output; if the client/provider supports it,
                # request native JSON formatting at the API layer (e.g., Ollama "format": "json").
                try:
                    response = self._client.complete(
                        prompt=artifact.prompt,
                        temperature=self._config.temperature,
                        model=self._config.interpreter_model,
                        response_format="json",
                    )
                except TypeError:
                    response = self._client.complete(
                        prompt=artifact.prompt,
                        temperature=self._config.temperature,
                        model=self._config.interpreter_model,
                    )
            except Exception as exc:  # pragma: no cover - transport level failure
                artifact.status = PhaseStatus.FAILED
                artifact.completed_at = self._now()
                artifact.human_notes = f"Gather phase failed: {exc}"
                failure_event = self._event(
                    kind=StrategyEventKind.NOTE,
                    message="Gather phase failed",
                    phase=artifact.phase.value,
                    iteration=iteration_index,
                    data={"error": str(exc)},
                )
                self.emit(failure_event)
                events.append(failure_event)
                return events

            response_text = response.strip()
            try:
                parsed = self._parse_gather_response(response_text)
                last_error = None
                break
            except ValueError as exc:
                parsed = None
                last_error = str(exc)
                # retry with a stronger constraint suffix
                artifact.prompt = (
                    base_prompt
                    + "\n\nIMPORTANT: Your previous response was invalid. Output ONLY the JSON object (no prose, no code fences), matching the schema exactly."
                )

        # restore original prompt so the trace remains stable
        artifact.prompt = base_prompt
        artifact.response = response_text
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["gather"] = {
            "attempts": attempts,
            "parseError": last_error,
        }

        if parsed is None:
            parsed = {"needs_more_context": False, "requests": []}
            artifact.human_notes = (
                "Gather stage did not return parseable JSON after 3 attempts; continuing without additional context."
            )

        enforced_reason: Optional[str]
        parsed, enforced_reason = self._enforce_gather_structural_requirements(
            request=request,
            iteration=iteration,
            gather_request=parsed,
            context_window=self._focused_context_window(request),
        )
        machine_checks["gather"]["enforced"] = enforced_reason is not None
        machine_checks["gather"]["enforcementReason"] = enforced_reason

        machine_checks["gather_request"] = parsed
        gathered_text, gathered_details = self._collect_gathered_context(request, parsed)
        machine_checks["gathered_context_text"] = gathered_text
        machine_checks["gathered_context"] = gathered_details
        self._record_iteration_telemetry(
            iteration,
            "gather",
            {
                "request": parsed,
                "collected": gathered_details,
            },
            append=True,
        )

        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Gather phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={
                "characters": len(artifact.response or ""),
                "gatheredCharacters": len(gathered_text or ""),
            },
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    @staticmethod
    def _context_looks_like_import_header(context_window: str) -> bool:
        """Best-effort heuristic for whether the current context includes a file header/import area."""

        lowered = (context_window or "").lower()
        return any(
            marker in lowered
            for marker in (
                "import ",
                "#include",
                "using ",
                "package ",
                "module ",
                "require(",
                "from ",
            )
        )

    @staticmethod
    def _planning_mentions_import_edit(planning_text: str) -> bool:
        lowered = (planning_text or "").lower()
        return any(
            token in lowered
            for token in (
                " add the import",
                " add an import",
                "missing import",
                "import statement",
                "#include",
                "using ",
            )
        )

    def _enforce_gather_structural_requirements(
        self,
        *,
        request: GuidedLoopInputs,
        iteration: GuidedIterationArtifact,
        gather_request: Dict[str, Any],
        context_window: str,
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """Apply deterministic-application guardrails when the model under-requests context."""

        if bool(gather_request.get("needs_more_context")):
            return gather_request, None

        planning_text = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
        if not planning_text:
            return gather_request, None

        planning_mentions_import = self._planning_mentions_import_edit(planning_text)
        context_has_header = self._context_looks_like_import_header(context_window)
        if planning_mentions_import and not context_has_header:
            enforced_reason = (
                "Enforced deterministic-application rule: planning indicates an import/header edit, "
                "but the current context window does not include the file header."
            )

            raw_requests = gather_request.get("requests")
            normalized_requests: list[dict[str, Any]] = []
            if isinstance(raw_requests, list):
                normalized_requests = [req for req in raw_requests if isinstance(req, dict)]

            if not any(req.get("category") == "IMPORTS_NAMESPACE" for req in normalized_requests):
                normalized_requests.append(
                    {
                        "category": "IMPORTS_NAMESPACE",
                        "target": None,
                        "reason": "Need the file header/imports to apply the planned import edit deterministically.",
                    }
                )

            why_text = self._coerce_string(gather_request.get("why"))
            why_text = (why_text or "").strip()
            if why_text:
                why_text = f"{why_text} {enforced_reason}"
            else:
                why_text = enforced_reason

            updated = dict(gather_request)
            updated["needs_more_context"] = True
            updated["why"] = why_text
            updated["requests"] = normalized_requests
            return updated, enforced_reason

        return gather_request, None

    def _execute_propose(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Propose phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.patch_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Propose phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        artifact.response = response.strip()
        if not artifact.response:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Proposal response was empty."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Propose phase failed: empty response",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        machine_checks = self._ensure_machine_checks_dict(artifact)
        machine_checks["proposal"] = artifact.response
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Propose phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_generate_patch(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> List[StrategyEvent]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Generate Patch phase",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=self._config.patch_model,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = f"Generate Patch phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Generate Patch phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return events
        artifact.response = response.strip()
        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Generate Patch phase completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={"characters": len(artifact.response)},
        )
        self.emit(completion_event)
        events.append(completion_event)
        return events

    def _execute_critique(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        iteration_index: int,
        request: GuidedLoopInputs,
    ) -> tuple[List[StrategyEvent], IterationOutcome | None]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        events: List[StrategyEvent] = []
        artifact.status = PhaseStatus.RUNNING
        artifact.started_at = self._now()
        start_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Starting Critique checks",
            phase=artifact.phase.value,
            iteration=iteration_index,
        )
        self.emit(start_event)
        events.append(start_event)

        diff_text = self._find_phase_response(iteration, GuidedPhase.GENERATE_PATCH)
        if not diff_text:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Generate Patch did not produce a diff to critique."
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique skipped: missing diff",
                phase=artifact.phase.value,
                iteration=iteration_index,
            )
            iteration.failure_reason = "missing-diff"
            self.emit(failure_event)
            events.append(failure_event)
            return events, IterationOutcome(
                diff_text=None,
                patch_applied=False,
                patch_diagnostics="No diff available",
                critique_feedback=artifact.response or artifact.human_notes,
            )

        diff_stats = self._summarize_diff(diff_text)
        replacement_blocks = self._parse_replacement_blocks(diff_text)
        artifact.machine_checks = {
            "diffStats": diff_stats,
        }
        artifact.metrics = {
            "diff_added": float(diff_stats["added_lines"]),
            "diff_removed": float(diff_stats["removed_lines"]),
            "diff_hunks": float(diff_stats["hunks"]),
        }

        experiment_summary = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
        active_hypothesis_text = experiment_summary or self._experiment_summary_placeholder()
        error_text = request.error_text or "(error unavailable)"
        history_context = iteration.history_context or self._history_placeholder()
        pre_span, post_span = self._diff_spans(diff_text, source_text=request.source_text)
        before_snippet = self._critique_snippet(
            request.source_text,
            pre_span,
            fallback=self._focused_context_window(request),
        )
        outcome = IterationOutcome(diff_text=diff_text, critique_feedback=artifact.response)
        outcome.diff_span = pre_span

        if diff_stats["hunks"] == 0:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Diff template invalid: no ORIGINAL/CHANGED blocks or @@ hunks were found."
            iteration.failure_reason = "empty-diff"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: malformed diff template",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"diff_excerpt": diff_text[:200]},
            )
            self.emit(failure_event)
            events.append(failure_event)
            outcome.patch_diagnostics = "Diff template missing ORIGINAL/CHANGED blocks"
            after_snippet = "Patched output unavailable because the diff template had no ORIGINAL/CHANGED blocks."
            self._finalize_critique_response(
                artifact,
                iteration_index,
                events,
                applied=False,
                history_context=history_context,
                error_text=error_text,
                active_hypothesis_text=active_hypothesis_text,
                before_snippet=before_snippet,
                after_snippet=after_snippet,
                diff_text=diff_text,
                diff_stats=diff_stats,
                outcome=outcome,
            )
            return events, outcome

        patched_text, applied, patch_message, span_override = self._apply_diff_text(
            request,
            diff_text,
            replacement_blocks,
        )
        if span_override:
            pre_span, post_span = span_override
            outcome.diff_span = pre_span
        artifact.machine_checks["patchApplication"] = {
            "applied": applied,
            "message": patch_message,
        }
        outcome.patch_applied = applied
        outcome.patch_diagnostics = patch_message
        if applied:
            outcome.patched_text = patched_text

        if not applied:
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            artifact.human_notes = "Patch application failed; queue another guided loop iteration to retry."
            iteration.failure_reason = "patch-apply"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique failed: patch application",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"diagnostics": patch_message},
            )
            self.emit(failure_event)
            events.append(failure_event)
            after_snippet = "Patched output unavailable because the diff could not be applied."
            self._finalize_critique_response(
                artifact,
                iteration_index,
                events,
                applied=False,
                history_context=history_context,
                error_text=error_text,
                active_hypothesis_text=active_hypothesis_text,
                before_snippet=before_snippet,
                after_snippet=after_snippet,
                diff_text=diff_text,
                diff_stats=diff_stats,
                outcome=outcome,
            )
            return events, outcome

        compile_result = None
        if self._config.compile_check and request.compile_command:
            compile_result = self._run_compile(request, patched_text)
            artifact.machine_checks["compile"] = dict(compile_result)
            outcome.compile_returncode = compile_result.get("returncode")
            outcome.compile_stdout = compile_result.get("stdout")
            outcome.compile_stderr = compile_result.get("stderr")
            fingerprint_source: Optional[str]
            compile_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Compile command completed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={
                    "command": compile_result.get("command"),
                    "returncode": compile_result.get("returncode"),
                },
            )
            self.emit(compile_event)
            events.append(compile_event)
            if compile_result.get("returncode") == 0:
                fingerprint_source = None
            else:
                fingerprint_source = compile_result.get("stderr") or compile_result.get("stdout")
                error_message = (fingerprint_source or "").strip()
                outcome.error_message = error_message or None
                if error_message:
                    outcome.error_location = self._detect_error_line(error_message, request.source_path.name)
            outcome.error_fingerprint = self._error_fingerprint(fingerprint_source)
            if compile_result.get("returncode") != 0:
                artifact.status = PhaseStatus.FAILED
                artifact.completed_at = self._now()
                artifact.human_notes = "Compile/Test command failed; provide diagnostics to the next guided loop iteration."
                iteration.failure_reason = f"compile-{compile_result.get('returncode')}"
                failure_event = self._event(
                    kind=StrategyEventKind.NOTE,
                    message="Critique failed: compile",
                    phase=artifact.phase.value,
                    iteration=iteration_index,
                    data={
                        "returncode": compile_result.get("returncode"),
                        "stderr": compile_result.get("stderr", "")[:500],
                    },
                )
                self.emit(failure_event)
                events.append(failure_event)
                after_snippet = self._critique_snippet(
                    patched_text,
                    post_span,
                    fallback="Patched output unavailable.",
                )
                self._finalize_critique_response(
                    artifact,
                    iteration_index,
                    events,
                    applied=True,
                    history_context=history_context,
                    error_text=error_text,
                    active_hypothesis_text=active_hypothesis_text,
                    before_snippet=before_snippet,
                    after_snippet=after_snippet,
                    diff_text=diff_text,
                    diff_stats=diff_stats,
                    outcome=outcome,
                )
                return events, outcome

        artifact.status = PhaseStatus.COMPLETED
        artifact.completed_at = self._now()
        after_snippet = self._critique_snippet(
            patched_text,
            post_span,
            fallback="Patched output unavailable.",
        )
        self._finalize_critique_response(
            artifact,
            iteration_index,
            events,
            applied=True,
            history_context=history_context,
            error_text=error_text,
            active_hypothesis_text=active_hypothesis_text,
            before_snippet=before_snippet,
            after_snippet=after_snippet,
            diff_text=diff_text,
            diff_stats=diff_stats,
            outcome=outcome,
        )
        iteration.failure_reason = None
        iteration.accepted = outcome.patch_applied and (
            not self._config.compile_check or not request.compile_command or outcome.compile_success
        )
        completion_event = self._event(
            kind=StrategyEventKind.PHASE_TRANSITION,
            message="Critique checks completed",
            phase=artifact.phase.value,
            iteration=iteration_index,
            data={
                "patch_applied": outcome.patch_applied,
                "compile_success": outcome.compile_success,
            },
        )
        self.emit(completion_event)
        events.append(completion_event)
        if not outcome.critique_feedback:
            outcome.critique_feedback = artifact.response or artifact.human_notes
        return events, outcome

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _prepare_phase_prompt(
        self,
        artifact: PhaseArtifact,
        iteration: GuidedIterationArtifact,
        request: GuidedLoopInputs,
        *,
        prior_outcome: IterationOutcome | None,
        history_context: str,
    ) -> None:
        critique_feedback = prior_outcome.critique_feedback if prior_outcome else self._critique_placeholder()
        previous_diff = (
            prior_outcome.diff_text if (prior_outcome and prior_outcome.diff_text) else self._previous_diff_placeholder()
        )
        context_override = self._focused_context_window(request)
        prior_patch_summary = self._format_prior_patch_summary(prior_outcome)
        is_refine_iteration = iteration.kind == "refine"
        refinement_context_text = self._refinement_context_placeholder()
        if is_refine_iteration:
            refinement_context_text = self._build_refinement_context(prior_outcome)

        if getattr(iteration, "include_full_critiques", False):
            full_transcript = self._critique_history_text()
            if full_transcript:
                critique_feedback = full_transcript

        phase_history_context = history_context
        phase_previous_diff = previous_diff
        phase_critique_feedback = critique_feedback
        phase_prior_patch_summary = prior_patch_summary

        if artifact.phase == GuidedPhase.DIAGNOSE:
            artifact.prompt = self._render_prompt(
                GuidedPhase.DIAGNOSE,
                request,
                context_override=context_override,
                extra={
                    "critique_feedback": phase_critique_feedback,
                    "previous_diff": phase_previous_diff,
                    "history_context": phase_history_context,
                    "prior_patch_summary": phase_prior_patch_summary,
                },
            )
        elif artifact.phase == GuidedPhase.PLANNING:
            diagnosis_output = self._find_phase_response(iteration, GuidedPhase.DIAGNOSE)
            if not diagnosis_output:
                diagnosis_output = self._latest_diagnosis_output
            critique_transcript = self._critique_history_text()
            artifact.prompt = self._render_prompt(
                GuidedPhase.PLANNING,
                request,
                context_override=context_override,
                extra={
                    "diagnosis_output": diagnosis_output or self._diagnosis_output_placeholder(),
                    "critique_output": critique_transcript or self._critique_output_placeholder(),
                },
            )
        elif artifact.phase == GuidedPhase.PROPOSE:
            experiment_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            gathered_context = self._coerce_string(self._find_gathered_context(iteration))
            artifact.prompt = self._render_prompt(
                GuidedPhase.PROPOSE,
                request,
                context_override=context_override,
                extra={
                    "experiment_summary": experiment_result or self._experiment_summary_placeholder(),
                    "gathered_context": gathered_context or self._gathered_context_placeholder(),
                    "critique_feedback": phase_critique_feedback,
                    "history_context": phase_history_context,
                    "previous_diff": phase_previous_diff,
                    "prior_patch_summary": phase_prior_patch_summary,
                    "refinement_context": refinement_context_text,
                },
            )
        elif artifact.phase == GuidedPhase.GATHER:
            experiment_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            artifact.prompt = self._render_prompt(
                GuidedPhase.GATHER,
                request,
                context_override=context_override,
                extra={
                    "experiment_summary": experiment_result or self._experiment_summary_placeholder(),
                },
            )
        elif artifact.phase == GuidedPhase.GENERATE_PATCH:
            planning_result = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PLANNING))
            active_hypothesis_text = planning_result or self._experiment_summary_placeholder()
            proposal_summary = self._coerce_string(self._find_phase_response(iteration, GuidedPhase.PROPOSE))
            gathered_context = self._coerce_string(self._find_gathered_context(iteration))
            artifact.prompt = self._render_prompt(
                GuidedPhase.GENERATE_PATCH,
                request,
                context_override=context_override,
                extra={
                    "diagnosis": active_hypothesis_text,
                    "diagnosis_explanation": active_hypothesis_text,
                    "proposal": proposal_summary or self._proposal_placeholder(),
                    "gathered_context": gathered_context or self._gathered_context_placeholder(),
                    "previous_diff": phase_previous_diff,
                    "prior_patch_summary": phase_prior_patch_summary,
                    "refinement_context": refinement_context_text,
                },
            )

    def _format_prior_patch_summary(self, prior_outcome: IterationOutcome | None, *, max_chars: int = 4000) -> str:
        placeholder = self._prior_patch_placeholder()
        if not prior_outcome:
            return placeholder
        if prior_outcome.diff_text:
            diff_text = prior_outcome.diff_text.strip()
            if not diff_text:
                return placeholder
            if len(diff_text) > max_chars:
                truncated = diff_text[:max_chars].rstrip()
                return f"{truncated}\n…"
            return diff_text
        diagnostics = (prior_outcome.patch_diagnostics or "").strip()
        if diagnostics:
            return diagnostics
        return placeholder

    def _build_refinement_context(self, prior_outcome: IterationOutcome | None) -> str:
        return "Refinement iterations reuse the most recent Diagnose output; do not rerun Diagnose."

    def _critique_history_text(self, limit: Optional[int] = None) -> Optional[str]:
        if not self._critique_transcripts:
            return None
        transcripts = self._critique_transcripts[-limit:] if limit else self._critique_transcripts
        separator = "\n\n---\n\n"
        return separator.join(transcripts)

    def _find_phase_response(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[str]:
        for artifact in iteration.phases:
            if artifact.phase == phase and artifact.response:
                return artifact.response
        return None

    def _find_phase_artifact(self, iteration: GuidedIterationArtifact, phase: GuidedPhase) -> Optional[PhaseArtifact]:
        for artifact in iteration.phases:
            if artifact.phase == phase:
                return artifact
        return None

    def _find_gathered_context(self, iteration: GuidedIterationArtifact) -> Optional[str]:
        artifact = self._find_phase_artifact(iteration, GuidedPhase.GATHER)
        if not artifact or not isinstance(artifact.machine_checks, Mapping):
            return None
        gathered = artifact.machine_checks.get("gathered_context_text")
        return gathered if isinstance(gathered, str) else None

    @staticmethod
    def _coerce_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            text = value
        elif isinstance(value, (int, float)):
            text = str(value)
        else:
            text = str(value)
        stripped = text.strip()
        return stripped or None

    @staticmethod
    def _record_iteration_telemetry(
        iteration: GuidedIterationArtifact | None,
        key: str,
        payload: Any,
        *,
        append: bool = False,
    ) -> None:
        if not iteration:
            return
        if iteration.telemetry is None:
            iteration.telemetry = {}
        if append:
            bucket = iteration.telemetry.setdefault(key, [])
            bucket.append(payload)
        else:
            iteration.telemetry[key] = payload

    def _record_critique_transcript(self, transcript: Optional[str]) -> None:
        if transcript:
            self._critique_transcripts.append(transcript)
    def _post_iteration_evaluation(
        self,
        iteration: GuidedIterationArtifact,
        outcome: IterationOutcome,
        previous_outcome: IterationOutcome | None,
    ) -> List[StrategyEvent]:
        events: List[StrategyEvent] = []
        if not outcome:
            return events

        stall_summary = self._detect_stall(previous_outcome, outcome)
        if stall_summary:
            iteration.failure_reason = "stall"
            self._record_iteration_telemetry(iteration, "stall", stall_summary, append=True)
            stall_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Stall detected: diff and error signature repeated",
                iteration=iteration.index,
                data=stall_summary,
            )
            self.emit(stall_event)
            events.append(stall_event)
            return events

        prev_fp = outcome.previous_error_fingerprint
        curr_fp = outcome.error_fingerprint
        if prev_fp is not None and curr_fp is not None and prev_fp == curr_fp:
            iteration.failure_reason = iteration.failure_reason or "unchanged-error"
            payload = {"previous": prev_fp, "current": curr_fp}
            self._record_iteration_telemetry(iteration, "unchangedError", payload, append=True)
            unchanged_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Error signature unchanged after patch",
                iteration=iteration.index,
                data=payload,
            )
            self.emit(unchanged_event)
            events.append(unchanged_event)
            return events

        return events

    def _detect_stall(
        self,
        previous_outcome: IterationOutcome | None,
        current_outcome: IterationOutcome | None,
    ) -> Optional[Dict[str, Any]]:
        prev_signature = self._stall_signature(previous_outcome)
        curr_signature = self._stall_signature(current_outcome)
        if not prev_signature or not curr_signature:
            return None
        if prev_signature != curr_signature:
            return None
        message, location, diff_span = curr_signature
        return {
            "errorMessage": message,
            "errorLocation": location,
            "diffSpan": list(diff_span),
        }

    def _stall_signature(self, outcome: IterationOutcome | None) -> Optional[Tuple[str, Optional[int], Tuple[int, int]]]:
        if not outcome or not outcome.patch_applied:
            return None
        if outcome.compile_returncode in (None, 0):
            return None
        if not outcome.diff_span:
            return None
        message = outcome.error_message or outcome.compile_stderr or outcome.compile_stdout or outcome.error_fingerprint
        if not message:
            return None
        normalized_message = re.sub(r"\s+", " ", message.strip())
        if not normalized_message:
            return None
        return normalized_message, outcome.error_location, outcome.diff_span

    @staticmethod
    def _ensure_machine_checks_dict(artifact: PhaseArtifact) -> Dict[str, Any]:
        if isinstance(artifact.machine_checks, dict):
            return artifact.machine_checks
        materialized = dict(artifact.machine_checks or {})
        artifact.machine_checks = materialized
        return materialized


    @staticmethod
    def _error_fingerprint(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return None
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _diagnosis_placeholder() -> str:
        return "Diagnosis not available yet; run the Diagnose phase first."

    @staticmethod
    def _diagnosis_explanation_placeholder() -> str:
        return "Diagnosis rationale not available yet; run the Diagnose phase first."

    @staticmethod
    def _diagnosis_output_placeholder() -> str:
        return "Diagnose phase output unavailable yet."

    @staticmethod
    def _proposal_placeholder() -> str:
        return "Proposal not available yet; run the Propose phase first."

    @staticmethod
    def _experiment_summary_placeholder() -> str:
        return "Experiment phase output unavailable yet."

    @staticmethod
    def _critique_output_placeholder() -> str:
        return "No critique transcripts are available yet."

    @staticmethod
    def _patch_diagnostics_placeholder() -> str:
        return "No patch diagnostics available yet."

    @staticmethod
    def _critique_placeholder() -> str:
        return "No prior critique feedback yet; this is the initial attempt."

    @staticmethod
    def _previous_diff_placeholder() -> str:
        return "No previous replacement attempt has been recorded."

    @staticmethod
    def _prior_patch_placeholder() -> str:
        return "No prior suggested patch is available yet."

    @staticmethod
    def _gathered_context_placeholder() -> str:
        return "No additional context gathered."

    def _parse_gather_response(self, text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("empty response")

        def strip_code_fences(raw: str) -> str:
            stripped = raw.strip()
            if not stripped.startswith("```"):
                return stripped
            # Drop the opening fence line (``` or ```json) and the closing fence if present.
            first_newline = stripped.find("\n")
            if first_newline != -1:
                stripped = stripped[first_newline + 1 :]
            stripped = stripped.strip()
            fence_idx = stripped.rfind("```")
            if fence_idx != -1:
                stripped = stripped[:fence_idx]
            return stripped.strip()

        def extract_first_json_object(raw: str) -> str:
            # Best-effort: if the model adds prose before/after, extract the first {...} block.
            candidate = raw.strip()
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return candidate
            return candidate[start : end + 1].strip()

        candidate = strip_code_fences(text)
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            candidate = extract_first_json_object(candidate)
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("root must be a JSON object")

        def norm_key(key: str) -> str:
            return re.sub(r"[^a-z0-9]", "", key.lower())

        normalized_payload: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(key, str):
                normalized_payload[norm_key(key)] = value

        needs = normalized_payload.get("needsmorecontext")
        why = normalized_payload.get("why")
        requests = normalized_payload.get("requests")
        if not isinstance(needs, bool):
            raise ValueError("needs_more_context must be boolean")
        if why is None:
            # Backwards compatibility with older traces / models; prompt requires it but we don't hard-fail.
            why = ""
        if not isinstance(why, str):
            raise ValueError("why must be a string")
        if not isinstance(requests, list):
            raise ValueError("requests must be a list")
        cleaned_requests: list[dict[str, Any]] = []
        for idx, item in enumerate(requests):
            if not isinstance(item, dict):
                raise ValueError(f"requests[{idx}] must be an object")
            item_norm: dict[str, Any] = {}
            for key, value in item.items():
                if isinstance(key, str):
                    item_norm[norm_key(key)] = value

            category = item_norm.get("category")
            if isinstance(category, str):
                category = category.strip().upper()
            if category not in self.GATHER_ALLOWED_CATEGORIES:
                raise ValueError(f"requests[{idx}].category must be one of {sorted(self.GATHER_ALLOWED_CATEGORIES)}")
            reason = item_norm.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"requests[{idx}].reason must be a non-empty string")
            target = item_norm.get("target")
            cleaned_target: Optional[dict[str, str]] = None
            if target is not None:
                if not isinstance(target, dict):
                    raise ValueError(f"requests[{idx}].target must be object or null")
                target_norm: dict[str, Any] = {}
                for key, value in target.items():
                    if isinstance(key, str):
                        target_norm[norm_key(key)] = value
                kind = target_norm.get("kind")
                name = target_norm.get("name")
                if isinstance(kind, str):
                    kind = kind.strip().lower()
                if kind not in self.GATHER_ALLOWED_TARGET_KINDS:
                    raise ValueError(
                        f"requests[{idx}].target.kind must be one of {sorted(self.GATHER_ALLOWED_TARGET_KINDS)}"
                    )
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(f"requests[{idx}].target.name must be a non-empty string")
                token = name.strip()
                if any(ch.isspace() for ch in token):
                    raise ValueError(f"requests[{idx}].target.name must be a single token")
                cleaned_target = {"kind": str(kind), "name": token}
            cleaned_requests.append(
                {
                    "category": str(category),
                    "target": cleaned_target,
                    "reason": reason.strip(),
                }
            )
        return {
            "needs_more_context": needs,
            "why": why.strip(),
            "requests": cleaned_requests,
        }

    def _collect_gathered_context(
        self,
        request: GuidedLoopInputs,
        gather_request: Mapping[str, Any],
        *,
        header_lines: int = 20,
        usage_radius: int = 3,
        scope_radius: int = 20,
        max_hits: int = 5,
        max_other_files: int = 3,
        max_file_chars: int = 120_000,
    ) -> tuple[str, Dict[str, Any]]:
        needs = gather_request.get("needs_more_context") is True
        why = gather_request.get("why") if isinstance(gather_request.get("why"), str) else ""
        requests = gather_request.get("requests") if isinstance(gather_request.get("requests"), list) else []
        if not needs or not requests:
            details: Dict[str, Any] = {"note": "no additional context requested"}
            if why.strip():
                details["why"] = why.strip()
            return "", details

        error_line = self._detect_error_line(request.error_text or "", request.source_path.name)
        all_lines = request.source_text.splitlines()
        total_lines = len(all_lines)

        def raw_window(start_line: int, end_line: int) -> str:
            start = max(1, start_line)
            end = min(total_lines, end_line)
            if start > end:
                return ""
            return "\n".join(all_lines[start - 1 : end]).rstrip()

        def numbered_window(start_line: int, end_line: int) -> str:
            start = max(1, start_line)
            end = min(total_lines, end_line)
            window = []
            for lineno in range(start, end + 1):
                raw = all_lines[lineno - 1]
                window.append(f"{lineno:4d} | {raw}")
            return "\n".join(window).rstrip()

        # Best-effort read of neighboring files for cross-file name resolution.
        other_files: list[tuple[str, str]] = []
        if request.source_path and request.source_path.exists():
            parent = request.source_path.parent
            ext = request.source_path.suffix.lower()
            candidates: list[Path] = []
            if ext in {".c", ".cc", ".cpp", ".cxx"}:
                candidates.extend(sorted(parent.glob("*.h")))
                candidates.extend(sorted(parent.glob(f"*{ext}")))
            elif ext in {".py"}:
                candidates.extend(sorted(parent.glob("*.py")))
            elif ext in {".ts", ".tsx", ".js", ".jsx"}:
                candidates.extend(sorted(parent.glob("*.ts")))
                candidates.extend(sorted(parent.glob("*.tsx")))
                candidates.extend(sorted(parent.glob("*.js")))
                candidates.extend(sorted(parent.glob("*.jsx")))
            elif ext in {".java"}:
                candidates.extend(sorted(parent.glob("*.java")))
            else:
                candidates.extend(sorted(parent.iterdir()))
            seen = set()
            for path in candidates:
                if len(other_files) >= max_other_files:
                    break
                if not path.is_file() or path == request.source_path:
                    continue
                if path.name in seen:
                    continue
                seen.add(path.name)
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if not text.strip():
                    continue
                other_files.append((path.name, text[:max_file_chars]))

        details: Dict[str, Any] = {
            "errorLine": error_line,
            "totalLines": total_lines,
            "why": why.strip(),
            "requested": [
                {
                    "category": item.get("category"),
                    "target": item.get("target"),
                    "reason": item.get("reason"),
                }
                for item in requests
                if isinstance(item, Mapping)
            ],
            "scannedOtherFiles": [name for name, _ in other_files],
        }

        sections: list[str] = []

        def infer_token_from_error_text() -> Optional[str]:
            # Prefer the enriched pointer summary inserted by _prepare_compile_error_text().
            text = request.error_text or ""
            if not text:
                return None
            match = re.search(r"current token:\s*identifier\s+'([^']+)'", text)
            if match:
                candidate = match.group(1).strip()
                if candidate and not any(ch.isspace() for ch in candidate):
                    return candidate
            match = re.search(r"current token:\s*identifier\s+\"([^\"]+)\"", text)
            if match:
                candidate = match.group(1).strip()
                if candidate and not any(ch.isspace() for ch in candidate):
                    return candidate
            return None

        # Determine token of interest (single token supported for now).
        token: Optional[str] = None
        for item in requests:
            if not isinstance(item, Mapping):
                continue
            target = item.get("target")
            if isinstance(target, Mapping):
                name = target.get("name")
                if isinstance(name, str) and name.strip():
                    token = name.strip()
                    break

        if token is None:
            token = infer_token_from_error_text()

        requested_categories = {
            item.get("category")
            for item in requests
            if isinstance(item, Mapping) and isinstance(item.get("category"), str)
        }

        if "FILE_CONTEXT" in requested_categories:
            sections.append(
                "FILE_CONTEXT:\n"
                + f"file={request.source_path.name}\n"
                + f"lines={total_lines}\n"
            )

        if "IMPORTS_NAMESPACE" in requested_categories:
            header_end = min(header_lines, total_lines)
            sections.append("IMPORTS_NAMESPACE (file header):\n" + numbered_window(1, header_end))

        if "ENCLOSING_SCOPE" in requested_categories and error_line:
            sections.append(
                "ENCLOSING_SCOPE (around error line):\n"
                + numbered_window(error_line - scope_radius, error_line + scope_radius)
            )

        def find_usages_in_text(text: str, *, file_label: str) -> list[str]:
            if not token:
                return []
            lines = text.splitlines()
            hits: list[str] = []
            for idx, line in enumerate(lines, start=1):
                if token in line:
                    start = max(1, idx - usage_radius)
                    end = min(len(lines), idx + usage_radius)
                    excerpt = []
                    excerpt.append(f"{file_label}:{idx}:")
                    for lineno in range(start, end + 1):
                        excerpt.append(f"{lineno:4d} | {lines[lineno - 1]}")
                    hits.append("\n".join(excerpt))
                    if len(hits) >= max_hits:
                        break
            return hits

        if token and "USAGE_CONTEXT" in requested_categories:
            hits = find_usages_in_text(request.source_text, file_label=request.source_path.name)
            for name, text in other_files:
                if len(hits) >= max_hits:
                    break
                hits.extend(find_usages_in_text(text, file_label=name))
                hits = hits[:max_hits]
            if hits:
                sections.append("USAGE_CONTEXT:\n" + "\n\n".join(hits))
            else:
                sections.append(f"USAGE_CONTEXT:\n(no occurrences of '{token}' found)")

        def find_declarations_in_text(text: str, *, file_label: str) -> list[str]:
            if not token:
                return []
            patterns = [
                re.compile(rf"\b(class|struct|enum|interface)\s+{re.escape(token)}\b"),
                re.compile(rf"\bdef\s+{re.escape(token)}\b"),
                re.compile(rf"\bfunction\s+{re.escape(token)}\b"),
                re.compile(rf"\btypedef\b.*\b{re.escape(token)}\b"),
                re.compile(rf"\b{re.escape(token)}\s*\("),
            ]
            lines = text.splitlines()
            hits: list[str] = []
            for idx, line in enumerate(lines, start=1):
                if any(p.search(line) for p in patterns):
                    hits.append(f"{file_label}:{idx}: {line.strip()}")
                    if len(hits) >= max_hits:
                        break
            return hits

        if token and "DECLARATION" in requested_categories:
            hits = find_declarations_in_text(request.source_text, file_label=request.source_path.name)
            for name, text in other_files:
                if len(hits) >= max_hits:
                    break
                hits.extend(find_declarations_in_text(text, file_label=name))
                hits = hits[:max_hits]
            if hits:
                sections.append("DECLARATION:\n" + "\n".join(hits))
            else:
                sections.append(f"DECLARATION:\n(no likely declarations of '{token}' found)")

        if token and "TYPE_CONTEXT" in requested_categories:
            # For now, reuse declaration heuristics; refine later per-language.
            hits = find_declarations_in_text(request.source_text, file_label=request.source_path.name)
            for name, text in other_files:
                if len(hits) >= max_hits:
                    break
                hits.extend(find_declarations_in_text(text, file_label=name))
                hits = hits[:max_hits]
            if hits:
                sections.append("TYPE_CONTEXT:\n" + "\n".join(hits))
            else:
                sections.append(f"TYPE_CONTEXT:\n(no type context found for '{token}')")

        combined = "\n\n".join(section for section in sections if section.strip()).strip()
        details["token"] = token
        details["sections"] = [section.split("\n", 1)[0] for section in sections]
        return combined, details

    @staticmethod
    def _history_placeholder() -> str:
        return "No prior iterations have run yet."

    @staticmethod
    def _refinement_context_placeholder() -> str:
        return "No refinement guidance for this iteration."

    def _context_for_phase(self, phase: GuidedPhase, request: GuidedLoopInputs) -> str:
        if phase in (GuidedPhase.DIAGNOSE, GuidedPhase.PROPOSE, GuidedPhase.GENERATE_PATCH):
            return self._focused_context_window(request)
        return self._default_context_slice(request)

    def _default_context_slice(self, request: GuidedLoopInputs, limit: int = 2000) -> str:
        source = request.source_text.strip()
        if not source:
            return "Source unavailable."
        if len(source) <= limit:
            return source
        return source[:limit].rstrip() + "\n…"

    def _focused_context_window(self, request: GuidedLoopInputs, radius: int = 5) -> str:
        source = request.source_text
        if not source:
            return "Source unavailable."
        lines = source.splitlines()
        if not lines:
            return "Source unavailable."
        error_line = self._detect_error_line(request.error_text or "", request.source_path.name)
        if error_line is None:
            start = 1
            end = min(len(lines), start + (radius * 2))
        else:
            center = max(1, min(error_line, len(lines)))
            start = max(1, center - radius)
            end = min(len(lines), center + radius)
        snippet = lines[start - 1 : end]
        return self._format_numbered_block(snippet, start)

    @staticmethod
    def _format_numbered_block(lines: Sequence[str], starting_line: int) -> str:
        formatted: List[str] = []
        line_no = starting_line
        for line in lines:
            formatted.append(f"{line_no:>4} | {line}")
            line_no += 1
        return "\n".join(formatted) if formatted else "Source unavailable."

    def _diff_spans(
        self,
        diff_text: str,
        *,
        source_text: str | None = None,
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        pattern = re.compile(r"@@ -(?P<start_a>\d+)(?:,(?P<len_a>\d+))? \+(?P<start_b>\d+)(?:,(?P<len_b>\d+))? @@")
        spans_a: List[tuple[int, int]] = []
        spans_b: List[tuple[int, int]] = []
        for line in diff_text.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            start_a = int(match.group("start_a"))
            len_a = int(match.group("len_a") or 1)
            start_b = int(match.group("start_b"))
            len_b = int(match.group("len_b") or 1)
            spans_a.append((start_a, start_a + max(len_a, 1) - 1))
            spans_b.append((start_b, start_b + max(len_b, 1) - 1))

        if spans_a or spans_b:
            return self._aggregate_spans(spans_a), self._aggregate_spans(spans_b)

        if source_text and "ORIGINAL LINES:" in diff_text and "NEW LINES:" in diff_text:
            return self._replacement_diff_spans(diff_text, source_text)

        return None, None

    @staticmethod
    def _aggregate_spans(spans: List[tuple[int, int]]) -> tuple[int, int] | None:
        if not spans:
            return None
        start = min(span[0] for span in spans)
        end = max(span[1] for span in spans)
        return start, end

    def _replacement_diff_spans(
        self,
        diff_text: str,
        source_text: str,
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        before_spans: List[tuple[int, int]] = []
        after_spans: List[tuple[int, int]] = []
        source_lines = source_text.splitlines()
        blocks = self._parse_replacement_blocks(diff_text)
        for original_lines, updated_lines in blocks:
            if not original_lines:
                continue
            index = self._patch_applier.find_context(source_lines, original_lines)
            if index is None:
                continue
            start_line = index + 1
            before_span = (start_line, start_line + max(len(original_lines), 1) - 1)
            after_span = (start_line, start_line + max(len(updated_lines), 1) - 1)
            before_spans.append(before_span)
            after_spans.append(after_span)
        return self._aggregate_spans(before_spans), self._aggregate_spans(after_spans)

    @staticmethod
    def _parse_replacement_blocks(diff_text: str) -> List[tuple[List[str], List[str]]]:
        blocks: List[tuple[List[str], List[str]]] = []
        text = diff_text.strip()
        for match in REPLACEMENT_BLOCK_PATTERN.finditer(text):
            original_lines = GuidedConvergenceStrategy._split_block_lines(match.group("original"))
            updated_lines = GuidedConvergenceStrategy._split_block_lines(match.group("updated"))
            blocks.append((original_lines, updated_lines))
        return blocks

    @staticmethod
    def _split_block_lines(block: str | None) -> List[str]:
        return normalize_replacement_block(block)

    def _apply_diff_text(
        self,
        request: GuidedLoopInputs,
        diff_text: str,
        replacement_blocks: List[tuple[List[str], List[str]]],
    ) -> tuple[Optional[str], bool, str, tuple[tuple[int, int] | None, tuple[int, int] | None] | None]:
        if replacement_blocks and all(original for original, _ in replacement_blocks):
            patched_text, applied, message, spans = self._apply_three_way_blocks(request, replacement_blocks)
            if applied:
                return patched_text, applied, message, spans

            # If the replacement targets lines outside the focused context fragment (for example imports at the
            # top of the file), the three-way merge will fail to locate the ORIGINAL block locally.
            # Fall back to a whole-file patch application so header edits can be applied deterministically.
            patched_text, applied = self._patch_applier.apply(request.source_text, diff_text)
            if not applied:
                return None, False, message, None
            spans = self._diff_spans(diff_text, source_text=request.source_text)
            return patched_text, True, f"Applied patch using whole-file matching after three-way merge failed: {message}", spans
        patched_text, applied = self._patch_applier.apply(request.source_text, diff_text)
        if not applied:
            return None, False, "Patch applier could not locate context", None
        spans = self._diff_spans(diff_text, source_text=request.source_text)
        return patched_text, True, "Patch applied successfully", spans

    def _apply_three_way_blocks(
        self,
        request: GuidedLoopInputs,
        replacement_blocks: List[tuple[List[str], List[str]]],
    ) -> tuple[Optional[str], bool, str, tuple[tuple[int, int] | None, tuple[int, int] | None] | None]:
        fragment_info = self._context_fragment_lines(request, radius=self.CONTEXT_RADIUS)
        if not fragment_info:
            return None, False, "Context fragment unavailable for merge.", None
        start_line, local_fragment = fragment_info
        original_length = len(local_fragment)
        if original_length == 0:
            return None, False, "Context fragment is empty; cannot run merge.", None
        base_fragment = list(local_fragment)
        build_success, target_fragment, build_diag = self._build_target_fragment(
            base_fragment,
            replacement_blocks,
        )
        if not build_success or target_fragment is None:
            message = build_diag or "Unable to construct target fragment for merge."
            return None, False, message, None
        merge_success, merged_fragment, merge_diag = self._merge_fragment_versions(
            base_fragment,
            local_fragment,
            target_fragment,
        )
        if not merge_success or merged_fragment is None:
            message = merge_diag or "Three-way merge failed while applying patch."
            return None, False, message, None
        source_lines = request.source_text.splitlines()
        start_idx = max(0, start_line - 1)
        end_idx = start_idx + original_length
        trailing_lines = source_lines[end_idx:]
        trailing_lines = self._collapse_suffix_overlap(merged_fragment, trailing_lines)
        updated_source = source_lines[:start_idx] + merged_fragment + trailing_lines
        trailing_newline = request.source_text.endswith("\n")
        patched_text = "\n".join(updated_source)
        if trailing_newline and not patched_text.endswith("\n"):
            patched_text += "\n"
        before_span = (start_line, start_line + original_length - 1) if original_length else None
        after_span = (start_line, start_line + len(merged_fragment) - 1) if merged_fragment else None
        span_tuple: tuple[tuple[int, int] | None, tuple[int, int] | None] = (before_span, after_span)
        return patched_text, True, "Three-way merge applied to context fragment.", span_tuple

    def _build_target_fragment(
        self,
        base_fragment: List[str],
        replacement_blocks: List[tuple[List[str], List[str]]],
    ) -> tuple[bool, Optional[List[str]], Optional[str]]:
        working = list(base_fragment)
        for index, (original_lines, updated_lines) in enumerate(replacement_blocks, start=1):
            if not original_lines:
                return False, None, "Replacement block missing ORIGINAL LINES; cannot merge."
            position = self._patch_applier.find_context(working, list(original_lines))
            if position is None:
                return False, None, f"Could not locate ORIGINAL block {index} within context fragment."
            before = working[:position]
            after = working[position + len(original_lines) :]
            working = before + list(updated_lines) + after
        return True, working, None

    def _merge_fragment_versions(
        self,
        base_fragment: Sequence[str],
        local_fragment: Sequence[str],
        target_fragment: Sequence[str],
    ) -> tuple[bool, Optional[List[str]], Optional[str]]:
        git_executable = shutil.which("git")
        if not git_executable:
            return False, None, "Git executable not found; cannot perform three-way merge."
        with tempfile.TemporaryDirectory(prefix="llm_patch_merge_") as tmpdir:
            tmp_path = Path(tmpdir)
            base_path = tmp_path / "base.txt"
            local_path = tmp_path / "local.txt"
            target_path = tmp_path / "target.txt"
            base_path.write_text(self._lines_to_text(base_fragment), encoding="utf-8")
            local_path.write_text(self._lines_to_text(local_fragment), encoding="utf-8")
            target_path.write_text(self._lines_to_text(target_fragment), encoding="utf-8")
            try:
                proc = subprocess.run(
                    [git_executable, "merge-file", "-p", str(local_path), str(base_path), str(target_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError as exc:  # pragma: no cover - defensive
                return False, None, f"git merge-file failed: {exc}"
        merged_output = proc.stdout
        stderr_text = proc.stderr.strip()
        if proc.returncode == 0:
            merged_lines = merged_output.splitlines()
            return True, merged_lines, None
        if proc.returncode == 1:
            diagnostic = stderr_text or "Merge conflict detected while applying patch."
            return False, None, diagnostic
        diagnostic = stderr_text or f"git merge-file exited with {proc.returncode}"
        return False, None, diagnostic

    def _collapse_suffix_overlap(
        self,
        target_fragment: Sequence[str],
        trailing_lines: Sequence[str],
    ) -> List[str]:
        if not target_fragment or not trailing_lines:
            return list(trailing_lines)
        max_overlap = min(
            self.SUFFIX_COLLAPSE_MAX_LINES,
            len(target_fragment),
            len(trailing_lines),
        )
        for overlap in range(max_overlap, 0, -1):
            suffix = target_fragment[-overlap:]
            prefix = trailing_lines[:overlap]
            if self._blocks_match(suffix, prefix):
                return list(trailing_lines[overlap:])
        return list(trailing_lines)

    def _blocks_match(self, suffix: Sequence[str], prefix: Sequence[str]) -> bool:
        if not suffix and not prefix:
            return True
        if len(suffix) != len(prefix):
            return False
        if all(self._normalize_line(a) == self._normalize_line(b) for a, b in zip(suffix, prefix)):
            return True
        text_a = "\n".join(suffix)
        text_b = "\n".join(prefix)
        if not text_a and not text_b:
            return True
        diffs = self._dmp.diff_main(text_a, text_b)
        self._dmp.diff_cleanupSemantic(diffs)
        equal_chars = sum(len(chunk) for op, chunk in diffs if op == 0)
        denominator = max(len(text_a), len(text_b), 1)
        similarity = equal_chars / denominator
        return similarity >= self.SUFFIX_COLLAPSE_SIMILARITY

    @staticmethod
    def _normalize_line(line: str) -> str:
        return " ".join(line.strip().split())

    def _context_fragment_lines(
        self,
        request: GuidedLoopInputs,
        *,
        radius: int,
    ) -> Optional[tuple[int, List[str]]]:
        source = request.source_text or ""
        if not source:
            return None
        lines = source.splitlines()
        if not lines:
            return None
        filename = request.source_path.name if request.source_path else ""
        error_line = self._detect_error_line(request.error_text or "", filename)
        if error_line is None:
            start = 1
            end = min(len(lines), start + (radius * 2))
        else:
            center = max(1, min(error_line, len(lines)))
            start = max(1, center - radius)
            end = min(len(lines), center + radius)
        fragment = lines[start - 1 : end]
        return start, fragment

    @staticmethod
    def _lines_to_text(lines: Sequence[str]) -> str:
        if not lines:
            return ""
        text = "\n".join(lines)
        if not text.endswith("\n"):
            text += "\n"
        return text

    def _critique_snippet(
        self,
        text: Optional[str],
        span: tuple[int, int] | None,
        *,
        radius: int = 5,
        fallback: str,
    ) -> str:
        if not text:
            return fallback
        lines = text.splitlines()
        if not lines:
            return fallback
        if not span:
            return fallback
        start = max(1, span[0] - radius)
        end = min(len(lines), span[1] + radius)
        excerpt = lines[start - 1 : end]
        return self._format_numbered_block(excerpt, start)

    def _build_critique_prompt(
        self,
        *,
        applied: bool,
        history_context: str,
        error_text: str,
        active_hypothesis_text: str,
        before_snippet: str,
        after_snippet: str,
        diff_text: str,
        validation_summary: str,
    ) -> str:
        header = (
            "Summarize the critique of the applied patch in three focused sections."
            if applied
            else "Summarize concerns about the proposed patch before it is applied."
        )
        checklist = (
            "Start with a header stating the hypothesis label and title.\n"
            "Then address each item in order:\n"
            "1) Outcome summary — Did the patch resolve the issue? Mention compile/test status.\n"
            "2) Could the patch be applied? — If not, explain why.\n"
            "3) In one word was the outcome successful? If not, declare the hypothesis to be 'REJECTED' ."
        )
        sections = [
            header,
            checklist,
            f"Validation summary:\n{validation_summary}",
            f"Recent iteration history:\n{history_context}",
            f"Original error:\n{error_text}",
            f"Active hypothesis summary:\n{active_hypothesis_text}",
            "Original Code before suggested replacement was applied:\n" + (before_snippet or "Source unavailable."),
            "Replacement block(s) that were applied:\n" + diff_text.strip(),
            "Updated Code after suggested replacement was applied:\n" + (after_snippet or "Source unavailable."),
        ]
        return "\n\n".join(sections).strip()

    def _finalize_critique_response(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        events: List[StrategyEvent],
        *,
        applied: bool,
        history_context: str,
        error_text: str,
        active_hypothesis_text: str,
        before_snippet: str,
        after_snippet: str,
        diff_text: str,
        diff_stats: Mapping[str, Any],
        outcome: IterationOutcome,
    ) -> None:
        summary = self._format_critique_summary(diff_stats, outcome)
        artifact.prompt = self._build_critique_prompt(
            applied=applied,
            history_context=history_context,
            error_text=error_text,
            active_hypothesis_text=active_hypothesis_text,
            before_snippet=before_snippet,
            after_snippet=after_snippet,
            diff_text=diff_text,
            validation_summary=summary,
        )
        critique_text = self._invoke_critique_model(artifact, iteration_index, events)
        if critique_text:
            normalized = critique_text.strip()
            artifact.response = f"{normalized}\n\nValidation summary: {summary}"
        else:
            artifact.response = summary
        outcome.critique_feedback = artifact.response
        self._record_critique_transcript(artifact.response)

    def _invoke_critique_model(
        self,
        artifact: PhaseArtifact,
        iteration_index: int,
        events: List[StrategyEvent],
    ) -> Optional[str]:
        if self._client is None:
            raise RuntimeError("GuidedConvergenceStrategy requires an LLM client to execute phases")
        model_name = (
            self._config.critique_model
            or self._config.patch_model
            or self._config.interpreter_model
        )
        try:
            response = self._client.complete(
                prompt=artifact.prompt,
                temperature=self._config.temperature,
                model=model_name,
            )
        except Exception as exc:  # pragma: no cover - transport level failure
            artifact.status = PhaseStatus.FAILED
            artifact.completed_at = self._now()
            if not artifact.human_notes:
                artifact.human_notes = f"Critique phase failed: {exc}"
            failure_event = self._event(
                kind=StrategyEventKind.NOTE,
                message="Critique phase failed",
                phase=artifact.phase.value,
                iteration=iteration_index,
                data={"error": str(exc)},
            )
            self.emit(failure_event)
            events.append(failure_event)
            return None
        return response.strip()

    @staticmethod
    def _detect_error_line(error_text: str, filename: str) -> Optional[int]:
        if not error_text:
            return None
        filename_pattern = re.compile(rf"{re.escape(filename)}:(\d+)") if filename else None
        generic_pattern = re.compile(r":(\d+):")
        keyword_pattern = re.compile(r"line\s+(\d+)", re.IGNORECASE)

        def extract_number(line: str) -> Optional[int]:
            match = filename_pattern.search(line) if filename_pattern else None
            if match:
                try:
                    return int(match.group(1))
                except ValueError:  # pragma: no cover - defensive
                    return None
            match = generic_pattern.search(line)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:  # pragma: no cover - defensive
                    return None
            match = keyword_pattern.search(line)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:  # pragma: no cover - defensive
                    return None
            return None

        lines = error_text.splitlines()
        priority_lines = [
            line
            for line in lines
            if GuidedConvergenceStrategy.ERROR_LINE_PATTERN.search(line)
            or GuidedConvergenceStrategy.WARNING_LINE_PATTERN.search(line)
        ]
        for line in priority_lines:
            extracted = extract_number(line)
            if extracted is not None:
                return extracted

        match = filename_pattern.search(error_text) if filename_pattern else None
        if match:
            try:
                return int(match.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        generic = generic_pattern.search(error_text)
        if generic:
            try:
                return int(generic.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        fallback = keyword_pattern.search(error_text)
        if fallback:
            try:
                return int(fallback.group(1))
            except ValueError:  # pragma: no cover - defensive
                return None
        return None

    # ------------------------------------------------------------------
    @staticmethod
    def _summarize_diff(diff_text: str) -> Dict[str, Any]:
        if "ORIGINAL LINES:" in diff_text and (
            "NEW LINES:" in diff_text or "CHANGED LINES:" in diff_text
        ):
            return GuidedConvergenceStrategy._summarize_replacement_blocks(diff_text)
        added = 0
        removed = 0
        hunks = 0
        for line in diff_text.splitlines():
            if line.startswith("@@"):
                hunks += 1
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1
        return {
            "added_lines": added,
            "removed_lines": removed,
            "hunks": hunks,
            "delete_only": added == 0 and removed > 0,
        }

    @staticmethod
    def _summarize_replacement_blocks(diff_text: str) -> Dict[str, Any]:
        blocks = GuidedConvergenceStrategy._parse_replacement_blocks(diff_text)
        hunks = len(blocks)
        added = sum(len(updated) for _, updated in blocks)
        removed = sum(len(original) for original, _ in blocks)
        return {
            "added_lines": added,
            "removed_lines": removed,
            "hunks": hunks,
            "delete_only": added == 0 and removed > 0,
        }

    def _run_compile(self, request: GuidedLoopInputs, patched_text: str) -> Dict[str, Any]:
        command = list(request.compile_command or [])
        if not command:
            return {"command": [], "returncode": None, "stdout": "", "stderr": ""}
        try:
            with tempfile.TemporaryDirectory(prefix="llm_patch_guided_") as tmpdir:
                tmp_path = Path(tmpdir)
                for rel_path in self._compile_target_paths(request, command):
                    destination = tmp_path / rel_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(patched_text, encoding="utf-8")
                proc = subprocess.run(
                    command,
                    cwd=str(tmp_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return {
                    "command": command,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
        except OSError as exc:  # pragma: no cover - defensive
            return {
                "command": command,
                "returncode": None,
                "stdout": "",
                "stderr": str(exc),
            }

    def _compile_target_paths(self, request: GuidedLoopInputs, command: Sequence[str]) -> List[Path]:
        """Return the relative file paths that should contain the patched source."""

        source_suffix = Path(request.source_path.name).suffix.lower()
        targets: List[Path] = []
        for token in command:
            if not token or token.startswith("-"):
                continue
            candidate = Path(token)
            suffix = candidate.suffix.lower()
            if not suffix or (source_suffix and suffix != source_suffix):
                continue
            if candidate.is_absolute():
                relative_candidate = Path(candidate.name)
            else:
                relative_candidate = candidate
            if relative_candidate not in targets:
                targets.append(relative_candidate)
        if not targets:
            targets.append(Path(request.source_path.name))
        return targets

    @staticmethod
    def _format_critique_summary(diff_stats: Mapping[str, Any], outcome: IterationOutcome) -> str:
        if not outcome.patch_applied:
            return outcome.patch_diagnostics or "The patch could not be applied to the source file."
        if outcome.compile_returncode is None:
            return "The diff was applied, and compile/test was skipped."
        if outcome.compile_success:
            return "The diff was applied and compile/test succeeded."
        return (
            "The diff was applied, but compile/test exited with return code "
            f"{outcome.compile_returncode}, so importantly the original issue still persists and we know the diff is erroneous."
        )

    @staticmethod
    def _result_notes(outcome: IterationOutcome | None) -> str:
        if outcome is None:
            return "Guided loop planned prompts but critique was not executed."
        if not outcome.patch_applied:
            return outcome.patch_diagnostics or "Patch application failed."
        if outcome.compile_returncode is None:
            return "Patch applied; compile/test skipped."
        if outcome.compile_success:
            return "Patch applied and compile/test succeeded."
        return f"Patch applied but compile/test exited with {outcome.compile_returncode}."
