"""
Configuration management.

Handles loading, saving, and accessing configuration settings.
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversionConfig:
    """Configuration for PDF conversion settings."""
    output_format: str = "markdown"
    ocr_enabled: bool = True
    ocr_languages: List[str] = field(default_factory=lambda: ["en", "zh-CN", "zh-TW"])


@dataclass
class MemoryConfig:
    """Configuration for memory management."""
    max_pages_in_memory: int = 5
    max_image_size_mb: int = 50
    enable_memory_monitoring: bool = True
    process_chunk_size: int = 3


@dataclass
class ProcessingConfig:
    """Configuration for processing settings."""
    max_workers: int = 4
    dpi: int = 200
    timeout_seconds: int = 300


@dataclass
class OutputConfig:
    """Configuration for output settings."""
    save_images: bool = True
    image_format: str = "png"
    extract_formulas_as_images: bool = True
    preserve_tables: bool = True
    preserve_code_blocks: bool = True


@dataclass
class LoggingConfig:
    """Configuration for logging settings."""
    level: str = "INFO"
    file: str = "pdf2md.log"
    console: bool = True


@dataclass
class Config:
    """Main configuration container."""

    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()

        if "conversion" in data:
            config.conversion = ConversionConfig(**data["conversion"])
        if "memory" in data:
            config.memory = MemoryConfig(**data["memory"])
        if "processing" in data:
            config.processing = ProcessingConfig(**data["processing"])
        if "output" in data:
            config.output = OutputConfig(**data["output"])
        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "conversion": asdict(self.conversion),
            "memory": asdict(self.memory),
            "processing": asdict(self.processing),
            "output": asdict(self.output),
            "logging": asdict(self.logging),
        }


def load_config(path: Optional[str | Path] = None) -> Config:
    """
    Load configuration from file.

    Args:
        path: Path to config file (YAML). If None, looks for config.yaml in current directory.

    Returns:
        Config object
    """
    if path is None:
        # Default config file locations
        default_paths = [
            Path("config.yaml"),
            Path(__file__).parent.parent.parent / "config.yaml",
        ]

        for default_path in default_paths:
            if default_path.exists():
                path = default_path
                break
        else:
            logger.info("No config file found, using defaults")
            return Config()

    config_path = Path(path)

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return Config()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        config = Config.from_dict(data)
        logger.info(f"Loaded configuration from {config_path}")
        return config

    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return Config()


def save_config(config: Config, path: str | Path) -> None:
    """
    Save configuration to file.

    Args:
        config: Config object to save
        path: Path to save config file (YAML)
    """
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Saved configuration to {config_path}")

    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")


def get_default_config() -> Config:
    """Get default configuration."""
    return Config()
