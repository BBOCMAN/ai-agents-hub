import logging
import os
import sys
from pathlib import Path
from typing import Optional
import yaml


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: Optional[bool] = True,
    config_file: str = "config.yaml"
) -> None:
    """
    Set up logging configuration for the SQL Agent.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        console_output: Whether to output logs to console
        config_file: Path to config file for settings
    """

    # Load config if available
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                logging_config = config.get('logging', {})

                # Use config values only if arguments were not provided
                if not log_level:
                    log_level = logging_config.get('level', "INFO")
                if not log_file:
                    log_file = logging_config.get('file')
                if console_output is None:
                    console_output = logging_config.get('console_output', True)
    except Exception:
        # If config loading fails, use defaults
        pass

    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear any existing handlers
    logger.handlers.clear()

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Log startup message
    logger.info("=" * 60)
    logger.info(f"SQL Agent Logger initialized - Level: {log_level}")
    logger.info(f"Console output: {console_output}")
    logger.info(f"Log file: {log_file if log_file else 'None'}")
    logger.info("=" * 60)



def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the logger (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class AgentLogger:
    """
    Custom logger class with agent-specific methods.
    Provides structured logging for different agent operations.
    """

    def __init__(self, name: str):
        self.logger = get_logger(name)

    def step(self, step_name: str, message: str) -> None:
        """Log an agent workflow step"""
        self.logger.info(f"STEP [{step_name.upper()}]: {message}")

    def plan(self, message: str) -> None:
        """Log planning phase"""
        self.logger.info(f"PLAN: {message}")

    def explore(self, message: str) -> None:
        """Log schema exploration"""
        self.logger.info(f"EXPLORE: {message}")

    def generate(self, message: str) -> None:
        """Log SQL generation"""
        self.logger.info(f"GENERATE: {message}")

    def execute(self, message: str) -> None:
        """Log query execution"""
        self.logger.info(f"EXECUTE: {message}")

    def recover(self, message: str) -> None:
        """Log error recovery"""
        self.logger.warning(f"RECOVER: {message}")

    def synthesize(self, message: str) -> None:
        """Log response synthesis"""
        self.logger.info(f"SYNTHESIZE: {message}")

    def error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log errors with optional exception details"""
        if error:
            self.logger.error(f"ERROR: {message} - {str(error)}")
        else:
            self.logger.error(f"ERROR: {message}")

    def success(self, message: str) -> None:
        """Log successful operations"""
        self.logger.info(f"SUCCESS: {message}")

    def debug_query(self, query: str) -> None:
        """Log SQL queries for debugging"""
        self.logger.debug(f"SQL: {query}")

    def debug_result(self, result: str) -> None:
        """Log query results for debugging"""
        self.logger.debug(f"RESULT: {result}")


def get_agent_logger(name: str) -> AgentLogger:
    """Get an AgentLogger instance"""
    return AgentLogger(name)