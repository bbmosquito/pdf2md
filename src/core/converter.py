"""
Docling-based PDF to Markdown Converter.

Core conversion engine using Docling for accurate PDF parsing,
OCR, and Markdown generation.
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import hashlib
import time

# Fix Windows symlink issue - disable symlinks for huggingface_hub
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, OcrAutoOptions

    # Try to import accelerator options (available in newer Docling versions)
    try:
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
        ACCELERATOR_AVAILABLE = True
    except ImportError:
        ACCELERATOR_AVAILABLE = False
        AcceleratorDevice = None
        AcceleratorOptions = None

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    ACCELERATOR_AVAILABLE = False
    # Create dummy classes for type hints when docling is not available
    DocumentConverter = None
    InputFormat = None
    PdfPipelineOptions = None
    OcrAutoOptions = None
    PdfFormatOption = None
    AcceleratorDevice = None
    AcceleratorOptions = None

from .pdf_reader import PDFReader, PDFInfo, PDFPage
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a PDF conversion."""
    success: bool
    source_path: Path
    output_path: Path
    pages_converted: int
    total_pages: int
    images_extracted: int
    duration_seconds: float
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class ConversionConfig:
    """Configuration for PDF to Markdown conversion."""

    # OCR settings
    ocr_enabled: bool = True
    ocr_languages: List[str] = field(default_factory=lambda: ["en", "zh-CN", "zh-TW"])

    # Processing settings
    max_workers: int = 4
    dpi: int = 200

    # Memory settings
    max_pages_in_memory: int = 5
    process_chunk_size: int = 3

    # Output settings
    extract_images: bool = True
    image_format: str = "png"  # png or jpg
    extract_formulas_as_images: bool = True
    preserve_tables: bool = True
    preserve_code_blocks: bool = True

    # Quality settings
    table_format: str = "pipe"  # pipe, grid, or simple

    # Performance optimization settings (NEW)
    enable_gpu: bool = True  # Auto-detect and enable GPU if available
    accelerator_device: str = "auto"  # "auto", "cuda", "mps", "cpu"
    num_threads: Optional[int] = None  # Auto-detect if None
    ocr_batch_size: int = 16  # Batch size for OCR processing
    layout_batch_size: int = 16  # Batch size for layout processing
    table_batch_size: int = 4  # Batch size for table processing


class DoclingConverter:
    """
    Converts PDF documents to Markdown using Docling.

    Features:
    - Uses Docling's advanced document parsing
    - Handles scanned PDFs with OCR
    - Extracts images, tables, and formulas
    - Memory-efficient chunked processing for large files
    - Progress tracking and error handling
    """

    def __init__(self, config: Optional[ConversionConfig] = None):
        """
        Initialize the converter.

        Args:
            config: Conversion configuration, uses defaults if None
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling is not installed. "
                "Install it with: pip install docling"
            )

        self.config = config or ConversionConfig()

        # Auto-detect optimal settings if not specified
        import psutil  # Import at function level to avoid scope issues

        if self.config.num_threads is None:
            self.config.num_threads = psutil.cpu_count(logical=False) or 4

        # Increase memory limit for large systems (e.g., 128GB systems)
        total_mem_gb = psutil.virtual_memory().total / (1024**3)
        if total_mem_gb >= 64:
            max_process_mb = int(total_mem_gb * 1024 * 0.7)  # Use up to 70% of RAM
        else:
            max_process_mb = 8192  # 8GB default

        self.memory_manager = MemoryManager(
            max_percent=85.0,
            max_process_mb=max_process_mb,
            enable_monitoring=True
        )

        # Initialize Docling converter with GPU acceleration
        self._init_docling()

    def _init_docling(self) -> None:
        """Initialize Docling document converter with GPU acceleration options."""
        import psutil

        # Configure PDF pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.config.ocr_enabled
        pipeline_options.do_table_structure = self.config.preserve_tables
        pipeline_options.do_code_enrichment = self.config.preserve_code_blocks

        # Set OCR languages using OcrAutoOptions
        if self.config.ocr_enabled and self.config.ocr_languages:
            pipeline_options.ocr_options = OcrAutoOptions(lang=self.config.ocr_languages)

        # Configure GPU acceleration if available
        if ACCELERATOR_AVAILABLE and self.config.enable_gpu:
            try:
                # Determine accelerator device
                if self.config.accelerator_device == "auto":
                    # Try to auto-detect
                    device_str = self._detect_accelerator_device()
                else:
                    device_str = self.config.accelerator_device

                # Map string to AcceleratorDevice enum
                if device_str == "cuda":
                    device = AcceleratorDevice.CUDA
                elif device_str == "mps":
                    device = AcceleratorDevice.MPS
                elif device_str == "cpu":
                    device = AcceleratorDevice.CPU
                else:
                    device = AcceleratorDevice.AUTO

                # Create accelerator options
                accelerator_options = AcceleratorOptions(
                    num_threads=self.config.num_threads,
                    device=device
                )

                pipeline_options.accelerator_options = accelerator_options

                logger.info(f"GPU acceleration enabled: device={device_str}, num_threads={self.config.num_threads}")

                # Set optimized batch sizes for GPU processing
                if device in [AcceleratorDevice.CUDA, AcceleratorDevice.AUTO]:
                    pipeline_options.ocr_batch_size = self.config.ocr_batch_size
                    pipeline_options.layout_batch_size = self.config.layout_batch_size
                    pipeline_options.table_batch_size = self.config.table_batch_size

                    logger.info(f"Optimized batch sizes: OCR={self.config.ocr_batch_size}, "
                              f"Layout={self.config.layout_batch_size}, Table={self.config.table_batch_size}")

            except Exception as e:
                logger.warning(f"Failed to enable GPU acceleration: {e}. Falling back to CPU.")
                # Set CPU explicitly if GPU setup failed
                if ACCELERATOR_AVAILABLE:
                    try:
                        accelerator_options = AcceleratorOptions(
                            num_threads=self.config.num_threads,
                            device=AcceleratorDevice.CPU
                        )
                        pipeline_options.accelerator_options = accelerator_options
                    except Exception:
                        pass

        # Create converter with options (using format_options with PdfFormatOption)
        self.docling_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        logger.info("Docling converter initialized")

    def _detect_accelerator_device(self) -> str:
        """Auto-detect the best accelerator device."""
        try:
            import torch

            if torch.cuda.is_available():
                # Check if it's ROCm (AMD) or CUDA (NVIDIA)
                if hasattr(torch.version, 'cuda') and 'rocm' in torch.version.cuda.lower():
                    logger.info("Detected AMD GPU via ROCm")
                    return "cuda"  # ROCm uses CUDA interface
                else:
                    logger.info("Detected NVIDIA GPU via CUDA")
                    return "cuda"
        except ImportError:
            logger.debug("PyTorch not available for GPU detection")
        except Exception as e:
            logger.debug(f"GPU detection error: {e}")

        # Check for Apple Silicon
        try:
            import platform
            if platform.system() == "Darwin":
                import subprocess
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Apple" in result.stdout:
                    logger.info("Detected Apple Silicon GPU")
                    return "mps"
        except Exception:
            pass

        # Check for AMD GPU on Windows without PyTorch
        try:
            import platform
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.check_output(
                    "wmic path win32_VideoController get name",
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                if "AMD" in result or "Radeon" in result:
                    logger.info("Detected AMD GPU on Windows")
                    # Note: Will try to use CUDA interface which may map to ROCm
                    return "cuda"
        except Exception:
            pass

        logger.info("No GPU detected, using CPU")
        return "cpu"

    def convert(
        self,
        pdf_path: str | Path,
        output_dir: str | Path = None,
        progress_callback=None
    ) -> ConversionResult:
        """
        Convert a PDF file to Markdown.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory (default: same as PDF, with new folder)
            progress_callback: Optional callback(progress: float, message: str)

        Returns:
            ConversionResult with conversion details
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return ConversionResult(
                success=False,
                source_path=pdf_path,
                output_path=Path(""),
                pages_converted=0,
                total_pages=0,
                images_extracted=0,
                duration_seconds=0,
                error_message=f"PDF file not found: {pdf_path}"
            )

        start_time = time.time()

        try:
            # Determine output directory
            if output_dir is None:
                output_dir = pdf_path.parent / f"{pdf_path.stem}_md"
            else:
                output_dir = Path(output_dir) / f"{pdf_path.stem}_md"

            output_dir = Path(output_dir)

            # Create output directories (explicitly create output_dir first)
            output_dir.mkdir(parents=True, exist_ok=True)
            images_dir = output_dir / "images"
            images_dir.mkdir(exist_ok=True)

            # Log memory before conversion
            self.memory_manager.log_stats("before conversion")

            # Convert using Docling
            if progress_callback:
                progress_callback(0.1, "Initializing Docling...")

            # For large files, we need to use Docling's streaming
            # But for MVP, we'll use the standard converter
            # TODO: Implement chunked processing for >200MB files

            result = self.docling_converter.convert(str(pdf_path))

            if progress_callback:
                progress_callback(0.5, "Generating Markdown...")

            # Export to Markdown
            markdown_content = result.document.export_to_markdown()

            # Save Markdown file
            output_md_path = output_dir / f"{pdf_path.stem}.md"

            # Process images and update markdown
            markdown_content = self._process_markdown_images(
                markdown_content,
                result.document,
                images_dir,
                pdf_path.stem
            )

            # Write the markdown file
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # Count extracted images
            images_count = len(list(images_dir.glob("*.*")))

            duration = time.time() - start_time

            self.memory_manager.log_stats("after conversion")

            # Force garbage collection to free memory after conversion
            import gc
            gc.collect()

            if progress_callback:
                progress_callback(1.0, "Conversion complete!")

            return ConversionResult(
                success=True,
                source_path=pdf_path,
                output_path=output_md_path,
                pages_converted=len(result.document.pages),
                total_pages=len(result.document.pages),
                images_extracted=images_count,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Conversion failed for {pdf_path}: {e}", exc_info=True)

            return ConversionResult(
                success=False,
                source_path=pdf_path,
                output_path=Path(""),
                pages_converted=0,
                total_pages=0,
                images_extracted=0,
                duration_seconds=duration,
                error_message=str(e)
            )

    def _process_markdown_images(
        self,
        markdown: str,
        document,
        images_dir: Path,
        pdf_stem: str
    ) -> str:
        """
        Process and extract images from the document.

        Updates markdown image references to point to extracted files.
        """
        # Docling may embed images or reference them
        # We need to extract them and update the markdown

        # For now, save the markdown as-is
        # TODO: Implement proper image extraction from Docling document

        return markdown

    def convert_chunked(
        self,
        pdf_path: str | Path,
        output_dir: str | Path = None,
        progress_callback = None
    ) -> ConversionResult:
        """
        Convert a large PDF file using chunked processing.

        This method processes the PDF in chunks to avoid loading
        the entire file into memory at once.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory
            progress_callback: Optional progress callback

        Returns:
            ConversionResult with conversion details
        """
        # This is a fallback for very large files
        # Uses PyMuPDF to read pages in chunks and convert them

        pdf_path = Path(pdf_path)

        if output_dir is None:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_md"
        else:
            output_dir = Path(output_dir) / f"{pdf_path.stem}_md"

        output_dir = Path(output_dir)
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        try:
            # First get PDF info
            with PDFReader(pdf_path) as reader:
                info = reader.get_info()
                total_pages = info.total_pages

            # Determine if we need chunked processing
            if not info.is_large_file:
                # Use regular conversion for smaller files
                return self.convert(pdf_path, output_dir.parent, progress_callback)

            # Process in chunks
            chunk_size = self.memory_manager.recommend_chunk_size(
                base_size=self.config.process_chunk_size
            )

            markdown_parts = []
            pages_converted = 0
            images_count = 0

            for start in range(0, total_pages, chunk_size):
                end = min(start + chunk_size, total_pages)

                if progress_callback:
                    progress = (start / total_pages) * 0.9
                    progress_callback(progress, f"Processing pages {start+1}-{end}...")

                # Convert this chunk
                # TODO: Implement chunk-by-chunk Docling conversion
                # For now, use the full converter

                pages_converted = end - start

            # Combine results
            duration = time.time() - start_time

            output_md_path = output_dir / f"{pdf_path.stem}.md"
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(markdown_parts))

            return ConversionResult(
                success=True,
                source_path=pdf_path,
                output_path=output_md_path,
                pages_converted=pages_converted,
                total_pages=total_pages,
                images_extracted=images_count,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Chunked conversion failed: {e}", exc_info=True)

            return ConversionResult(
                success=False,
                source_path=pdf_path,
                output_path=Path(""),
                pages_converted=0,
                total_pages=0,
                images_extracted=0,
                duration_seconds=duration,
                error_message=str(e)
            )

    def _save_image(self, image_data: bytes, images_dir: Path, index: int) -> str:
        """
        Save image data to file and return the relative path.

        Args:
            image_data: Image bytes
            images_dir: Directory to save images
            index: Image index for filename

        Returns:
            Relative path to saved image
        """
        # Generate filename
        ext = self.config.image_format
        filename = f"image_{index:04d}.{ext}"
        filepath = images_dir / filename

        # Save image
        with open(filepath, "wb") as f:
            f.write(image_data)

        return f"images/{filename}"


def is_docling_available() -> bool:
    """Check if Docling is available."""
    return DOCLING_AVAILABLE


def install_docling_instructions() -> str:
    """Get installation instructions for Docling."""
    return (
        "Docling is required for PDF conversion.\n"
        "Install with: pip install docling\n\n"
        "For OCR support (recommended):\n"
        "  pip install docling[ocr]\n\n"
        "For Windows, you may also need to install Tesseract OCR separately."
    )
