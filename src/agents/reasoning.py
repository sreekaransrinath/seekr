"""Reasoning and decision logging for agent transparency."""
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReasoningLevel(str, Enum):
    """Levels of reasoning."""

    PLANNING = "planning"
    DECISION = "decision"
    EXECUTION = "execution"
    VALIDATION = "validation"
    ERROR = "error"


class ReasoningEntry(BaseModel):
    """A single reasoning or decision entry."""

    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: ReasoningLevel = Field(..., description="Type of reasoning")
    task: str = Field(..., description="Task being performed")
    reasoning: str = Field(..., description="The reasoning or decision made")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    outcome: Optional[str] = Field(None, description="Outcome if applicable")


class ReasoningLogger:
    """Logger for transparent agent reasoning and decision-making."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize reasoning logger.

        Args:
            output_dir: Directory to write reasoning logs
        """
        self.output_dir = output_dir or Path("outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.entries: list[ReasoningEntry] = []
        self.current_log_file: Optional[Path] = None

    def log_planning(
        self,
        task: str,
        reasoning: str,
        context: Optional[dict] = None,
    ):
        """
        Log a planning decision.

        Args:
            task: Task being planned
            reasoning: Planning reasoning
            context: Additional context
        """
        self._log_entry(
            ReasoningEntry(
                level=ReasoningLevel.PLANNING,
                task=task,
                reasoning=reasoning,
                context=context or {},
            )
        )

    def log_decision(
        self,
        task: str,
        reasoning: str,
        outcome: str,
        context: Optional[dict] = None,
    ):
        """
        Log a decision made by the agent.

        Args:
            task: Task the decision is for
            reasoning: Why this decision was made
            outcome: What was decided
            context: Additional context
        """
        self._log_entry(
            ReasoningEntry(
                level=ReasoningLevel.DECISION,
                task=task,
                reasoning=reasoning,
                outcome=outcome,
                context=context or {},
            )
        )

    def log_execution(
        self,
        task: str,
        reasoning: str,
        outcome: Optional[str] = None,
        context: Optional[dict] = None,
    ):
        """
        Log execution of a task.

        Args:
            task: Task being executed
            reasoning: Why/how it's being executed
            outcome: Result if available
            context: Additional context
        """
        self._log_entry(
            ReasoningEntry(
                level=ReasoningLevel.EXECUTION,
                task=task,
                reasoning=reasoning,
                outcome=outcome,
                context=context or {},
            )
        )

    def log_validation(
        self,
        task: str,
        reasoning: str,
        outcome: str,
        context: Optional[dict] = None,
    ):
        """
        Log validation of results.

        Args:
            task: Task being validated
            reasoning: Validation reasoning
            outcome: Validation result
            context: Additional context
        """
        self._log_entry(
            ReasoningEntry(
                level=ReasoningLevel.VALIDATION,
                task=task,
                reasoning=reasoning,
                outcome=outcome,
                context=context or {},
            )
        )

    def log_error(
        self,
        task: str,
        reasoning: str,
        context: Optional[dict] = None,
    ):
        """
        Log an error or issue.

        Args:
            task: Task where error occurred
            reasoning: What went wrong and why
            context: Additional context
        """
        self._log_entry(
            ReasoningEntry(
                level=ReasoningLevel.ERROR,
                task=task,
                reasoning=reasoning,
                context=context or {},
            )
        )

    def _log_entry(self, entry: ReasoningEntry):
        """Add entry to log and write to file."""
        self.entries.append(entry)

        # Also print to console for real-time visibility
        print(f"\n[{entry.level.value.upper()}] {entry.task}")
        print(f"  → {entry.reasoning}")
        if entry.outcome:
            print(f"  ✓ {entry.outcome}")

    def save_to_file(self, filename: Optional[str] = None):
        """
        Save reasoning log to file.

        Args:
            filename: Output filename (default: agent_reasoning_<timestamp>.log)
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_reasoning_{timestamp}.log"

        log_file = self.output_dir / filename

        # Write as formatted text
        with open(log_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("AGENT REASONING LOG\n")
            f.write("=" * 80 + "\n\n")

            for entry in self.entries:
                f.write(f"[{entry.timestamp}] {entry.level.value.upper()}\n")
                f.write(f"Task: {entry.task}\n")
                f.write(f"Reasoning: {entry.reasoning}\n")
                if entry.outcome:
                    f.write(f"Outcome: {entry.outcome}\n")
                if entry.context:
                    f.write(f"Context: {json.dumps(entry.context, indent=2)}\n")
                f.write("-" * 80 + "\n\n")

        self.current_log_file = log_file
        print(f"\n✓ Reasoning log saved to: {log_file}")

    def save_to_json(self, filename: Optional[str] = None):
        """
        Save reasoning log as JSON.

        Args:
            filename: Output filename
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_reasoning_{timestamp}.json"

        log_file = self.output_dir / filename

        with open(log_file, "w") as f:
            json.dump(
                [entry.model_dump() for entry in self.entries],
                f,
                indent=2,
            )

        print(f"\n✓ Reasoning log (JSON) saved to: {log_file}")

    def get_summary(self) -> dict:
        """Get summary statistics of reasoning log."""
        return {
            "total_entries": len(self.entries),
            "by_level": {
                level.value: sum(1 for e in self.entries if e.level == level)
                for level in ReasoningLevel
            },
            "tasks": list(set(e.task for e in self.entries)),
        }
