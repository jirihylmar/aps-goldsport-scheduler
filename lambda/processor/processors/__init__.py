"""
GoldSport Scheduler - Processor Base Classes

This module defines the base classes for the processing pipeline.
Each processor transforms data through the pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger(__name__)


class Processor(ABC):
    """
    Base class for all pipeline processors.

    Each processor receives data, transforms it, and returns the result.
    Processors should be stateless and idempotent.
    """

    @property
    def name(self) -> str:
        """Return the processor name for logging."""
        return self.__class__.__name__

    @abstractmethod
    def process(self, data: dict) -> dict:
        """
        Process the data and return transformed result.

        Args:
            data: Dictionary containing pipeline state and data

        Returns:
            Dictionary with transformed data

        Raises:
            ProcessorError: If processing fails
        """
        raise NotImplementedError


class ProcessorError(Exception):
    """Exception raised when a processor fails."""

    def __init__(self, processor_name: str, message: str, original_error: Exception = None):
        self.processor_name = processor_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{processor_name}] {message}")
