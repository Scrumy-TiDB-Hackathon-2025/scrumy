"""
WebSocket Event Monitor
Utility for detecting duplicate events, validating event structures, and monitoring WebSocket communication patterns.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from websocket_events import WebSocketEventValidator, DEPRECATED_EVENT_NAMES

logger = logging.getLogger(__name__)

@dataclass
class EventRecord:
    """Record of a WebSocket event for monitoring purposes."""
    event_type: str
    timestamp: datetime
    data_hash: str
    source: str
    session_id: Optional[str] = None
    chunk_id: Optional[str] = None
    meeting_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class DuplicateDetection:
    """Configuration for duplicate event detection."""
    time_window_seconds: int = 5
    max_duplicates_allowed: int = 0  # 0 means any duplicate is flagged
    ignore_fields: List[str] = field(default_factory=lambda: ['timestamp', 'chunkId'])

class WebSocketEventMonitor:
    """Monitor and validate WebSocket events for duplicates and consistency issues."""

    def __init__(self, duplicate_config: Optional[DuplicateDetection] = None):
        self.duplicate_config = duplicate_config or DuplicateDetection()
        self.event_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.duplicate_counts: Dict[str, int] = defaultdict(int)
        self.deprecated_usage: Dict[str, int] = defaultdict(int)
        self.validation_errors: List[Dict] = []
        self.session_events: Dict[str, List[EventRecord]] = defaultdict(list)

        # Statistics
        self.stats = {
            'total_events': 0,
            'duplicates_detected': 0,
            'deprecated_events': 0,
            'validation_errors': 0,
            'unique_sessions': 0
        }

    def record_event(self, event_type: str, data: Dict, source: str = "unknown",
                    session_id: Optional[str] = None) -> Dict:
        """
        Record an event and perform duplicate detection and validation.

        Returns:
            Dictionary with monitoring results and recommendations
        """
        self.stats['total_events'] += 1

        # Create event record
        data_hash = self._hash_event_data(data)
        event_record = EventRecord(
            event_type=event_type,
            timestamp=datetime.now(),
            data_hash=data_hash,
            source=source,
            session_id=session_id,
            chunk_id=str(data.get('chunkId')) if data.get('chunkId') is not None else None,
            meeting_id=str(data.get('meetingId')) if data.get('meetingId') is not None else None
        )

        results = {
            'is_duplicate': False,
            'is_deprecated': False,
            'validation_errors': [],
            'recommendations': [],
            'event_record': event_record
        }

        # Check for deprecated events
        if event_type in DEPRECATED_EVENT_NAMES:
            self.deprecated_usage[event_type] += 1
            self.stats['deprecated_events'] += 1
            results['is_deprecated'] = True
            results['recommendations'].append(
                f"Use '{DEPRECATED_EVENT_NAMES[event_type]}' instead of '{event_type}'"
            )

        # Validate event structure
        is_valid, error_msg = WebSocketEventValidator.validate_event(event_type, data)
        if not is_valid:
            self.validation_errors.append({
                'event_type': event_type,
                'error': error_msg,
                'timestamp': datetime.now(),
                'source': source
            })
            self.stats['validation_errors'] += 1
            results['validation_errors'].append(error_msg)

        # Check for duplicates
        if self._is_duplicate_event(event_record):
            self.duplicate_counts[f"{event_type}:{data_hash}"] += 1
            self.stats['duplicates_detected'] += 1
            results['is_duplicate'] = True
            results['recommendations'].append(
                "Duplicate event detected - check for double message sending"
            )

        # Store event in history
        history_key = f"{source}:{event_type}"
        self.event_history[history_key].append(event_record)

        # Track session
        if session_id:
            self.session_events[session_id].append(event_record)
            self.stats['unique_sessions'] = len(self.session_events)

        # Log issues if any
        if results['is_duplicate'] or results['is_deprecated'] or results['validation_errors']:
            self._log_event_issues(event_record, results)

        return results

    def _hash_event_data(self, data: Dict) -> str:
        """Create a hash of event data for duplicate detection, ignoring specified fields."""
        filtered_data = {
            k: v for k, v in data.items()
            if k not in self.duplicate_config.ignore_fields
        }
        return str(hash(json.dumps(filtered_data, sort_keys=True)))

    def _is_duplicate_event(self, event_record: EventRecord) -> bool:
        """Check if this event is a duplicate within the configured time window."""
        cutoff_time = event_record.timestamp - timedelta(
            seconds=self.duplicate_config.time_window_seconds
        )

        # Check recent events of the same type from the same source
        history_key = f"{event_record.source}:{event_record.event_type}"
        recent_events = [
            e for e in self.event_history[history_key]
            if e.timestamp >= cutoff_time and e.data_hash == event_record.data_hash
        ]

        # An event is a duplicate if we already have the same data hash within the time window
        return len(recent_events) > self.duplicate_config.max_duplicates_allowed

    def _log_event_issues(self, event_record: EventRecord, results: Dict):
        """Log event issues for debugging."""
        issues = []
        if results['is_duplicate']:
            issues.append("DUPLICATE")
        if results['is_deprecated']:
            issues.append("DEPRECATED")
        if results['validation_errors']:
            issues.append(f"VALIDATION_ERROR: {'; '.join(results['validation_errors'])}")

        logger.warning(
            f"[WebSocket Monitor] Event Issues [{', '.join(issues)}] - "
            f"Type: {event_record.event_type}, Source: {event_record.source}, "
            f"Session: {event_record.session_id}, Time: {event_record.timestamp}"
        )

    def get_session_analysis(self, session_id: str) -> Dict:
        """Analyze events for a specific session."""
        if session_id not in self.session_events:
            return {'error': f'Session {session_id} not found'}

        events = self.session_events[session_id]
        event_types = defaultdict(int)
        duplicates = 0
        deprecated = 0

        for event in events:
            event_types[event.event_type] += 1
            # Check if this event was flagged as duplicate
            if self.duplicate_counts.get(f"{event.event_type}:{event.data_hash}", 0) > 0:
                duplicates += 1
            if event.event_type in DEPRECATED_EVENT_NAMES:
                deprecated += 1

        return {
            'session_id': session_id,
            'total_events': len(events),
            'event_types': dict(event_types),
            'duplicates': duplicates,
            'deprecated_events': deprecated,
            'first_event': events[0].timestamp if events else None,
            'last_event': events[-1].timestamp if events else None,
            'duration_minutes': (events[-1].timestamp - events[0].timestamp).total_seconds() / 60 if len(events) > 1 else 0
        }

    def get_duplicate_report(self) -> Dict:
        """Generate a report of all detected duplicates."""
        report = {
            'total_duplicates': self.stats['duplicates_detected'],
            'duplicate_patterns': {},
            'most_frequent_duplicates': []
        }

        # Group duplicates by pattern
        for key, count in self.duplicate_counts.items():
            if count > 0:
                event_type, data_hash = key.split(':', 1)
                if event_type not in report['duplicate_patterns']:
                    report['duplicate_patterns'][event_type] = []
                report['duplicate_patterns'][event_type].append({
                    'data_hash': data_hash,
                    'count': count
                })

        # Sort by frequency
        all_duplicates = [(k, v) for k, v in self.duplicate_counts.items() if v > 0]
        report['most_frequent_duplicates'] = sorted(
            all_duplicates, key=lambda x: x[1], reverse=True
        )[:10]

        return report

    def get_deprecated_usage_report(self) -> Dict:
        """Generate a report of deprecated event usage."""
        return {
            'total_deprecated': self.stats['deprecated_events'],
            'by_event_type': dict(self.deprecated_usage),
            'recommendations': {
                old: new for old, new in DEPRECATED_EVENT_NAMES.items()
                if old in self.deprecated_usage
            }
        }

    def get_validation_errors_report(self) -> List[Dict]:
        """Get all validation errors."""
        return self.validation_errors

    def get_comprehensive_report(self) -> Dict:
        """Generate a comprehensive monitoring report."""
        return {
            'summary': self.stats,
            'duplicates': self.get_duplicate_report(),
            'deprecated_usage': self.get_deprecated_usage_report(),
            'validation_errors': self.get_validation_errors_report(),
            'session_count': len(self.session_events),
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on monitoring data."""
        recommendations = []

        if self.stats['duplicates_detected'] > 0:
            recommendations.append(
                f"Found {self.stats['duplicates_detected']} duplicate events. "
                "Check WebSocket server for double message sending."
            )

        if self.stats['deprecated_events'] > 0:
            recommendations.append(
                f"Found {self.stats['deprecated_events']} deprecated events. "
                "Update code to use standardized event types."
            )

        if self.stats['validation_errors'] > 0:
            recommendations.append(
                f"Found {self.stats['validation_errors']} validation errors. "
                "Ensure event data includes all required fields."
            )

        # Check for unusual patterns
        if len(self.event_history) > 0:
            transcription_events = sum(
                len(events) for key, events in self.event_history.items()
                if 'TRANSCRIPTION_RESULT' in key or 'transcription_result' in key
            )
            if transcription_events > self.stats['total_events'] * 0.8:
                recommendations.append(
                    "High volume of transcription events detected. "
                    "Consider implementing event batching or throttling."
                )

        return recommendations

    def reset_monitoring(self):
        """Reset all monitoring data."""
        self.event_history.clear()
        self.duplicate_counts.clear()
        self.deprecated_usage.clear()
        self.validation_errors.clear()
        self.session_events.clear()
        self.stats = {
            'total_events': 0,
            'duplicates_detected': 0,
            'deprecated_events': 0,
            'validation_errors': 0,
            'unique_sessions': 0
        }


# Global monitor instance
global_monitor = WebSocketEventMonitor()

def monitor_event(event_type: str, data: Dict, source: str = "unknown",
                 session_id: Optional[str] = None) -> Dict:
    """Convenience function to monitor an event using the global monitor."""
    return global_monitor.record_event(event_type, data, source, session_id)

def get_monitoring_report() -> Dict:
    """Get comprehensive monitoring report from global monitor."""
    return global_monitor.get_comprehensive_report()

def reset_global_monitor():
    """Reset the global monitor."""
    global_monitor.reset_monitoring()
