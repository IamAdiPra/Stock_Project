"""
Centralized logging system for data quality audits and error tracking.
Maintains in-memory logs of ticker fetch failures for UI display.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, List, Dict

# Global in-memory store for data quality issues
_data_quality_log: List["DataQualityIssue"] = []


@dataclass
class DataQualityIssue:
    """Represents a single data fetch failure or quality problem."""

    ticker: str
    issue_type: Literal["fetch_failure", "validation_error", "incomplete_data"]
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.ticker}: {self.issue_type} - {self.error_message}"


def log_data_issue(
    ticker: str,
    issue_type: Literal["fetch_failure", "validation_error", "incomplete_data"],
    error_message: str
) -> None:
    """
    Log a data quality issue to the in-memory store.

    Args:
        ticker: Stock ticker symbol
        issue_type: Category of the issue
        error_message: Detailed error description
    """
    issue = DataQualityIssue(
        ticker=ticker,
        issue_type=issue_type,
        error_message=error_message
    )
    _data_quality_log.append(issue)


def get_data_quality_log() -> List[DataQualityIssue]:
    """
    Retrieve all logged data quality issues.

    Returns:
        List of DataQualityIssue objects
    """
    return _data_quality_log.copy()


def clear_data_quality_log() -> None:
    """Clear all logged issues (useful for session reset)."""
    _data_quality_log.clear()


def get_failure_summary() -> Dict[str, int]:
    """
    Get a summary count of issues by type.

    Returns:
        Dictionary mapping issue_type to count
    """
    summary: Dict[str, int] = {
        "fetch_failure": 0,
        "validation_error": 0,
        "incomplete_data": 0
    }

    for issue in _data_quality_log:
        summary[issue.issue_type] += 1

    return summary
