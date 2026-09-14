"""
MARL Environments for CA-RDL (XApp-RDL-F2).
Includes trace replay environment for non-synthetic telemetric trace execution.
"""

from .trace_replay_env import TraceReplayEnvironment

__all__ = ["TraceReplayEnvironment"]
