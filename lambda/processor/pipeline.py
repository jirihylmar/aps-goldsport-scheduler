"""
GoldSport Scheduler - Processing Pipeline

Orchestrates the data processing through a chain of processors.
"""

import logging
from typing import List
from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Orchestrates processing through a chain of processors.

    The pipeline runs each processor in sequence, passing the output
    of one processor as input to the next.
    """

    def __init__(self, processors: List[Processor]):
        """
        Initialize the pipeline with a list of processors.

        Args:
            processors: Ordered list of processors to execute
        """
        self.processors = processors

    def run(self, data: dict) -> dict:
        """
        Run all processors in sequence.

        Args:
            data: Initial data dictionary

        Returns:
            Final processed data dictionary

        Raises:
            ProcessorError: If any processor fails
        """
        logger.info(f"Starting pipeline with {len(self.processors)} processors")

        for processor in self.processors:
            logger.info(f"Running processor: {processor.name}")
            try:
                data = processor.process(data)
                logger.info(f"Processor {processor.name} completed")
            except ProcessorError:
                # Re-raise ProcessorErrors as-is
                raise
            except Exception as e:
                # Wrap other exceptions in ProcessorError
                logger.error(f"Processor {processor.name} failed: {e}")
                raise ProcessorError(processor.name, str(e), e)

        logger.info("Pipeline completed successfully")
        return data


class PipelineBuilder:
    """
    Builder for constructing pipelines with fluent interface.

    Example:
        pipeline = (PipelineBuilder()
            .add(ParseOrdersProcessor())
            .add(ValidateProcessor())
            .add(PrivacyProcessor())
            .build())
    """

    def __init__(self):
        self._processors: List[Processor] = []

    def add(self, processor: Processor) -> 'PipelineBuilder':
        """Add a processor to the pipeline."""
        self._processors.append(processor)
        return self

    def build(self) -> Pipeline:
        """Build and return the pipeline."""
        return Pipeline(self._processors)
