"""
PDF Reader for streaming large PDF files.

Uses PyMuPDF (fitz) to efficiently read PDFs page by page
without loading the entire file into memory.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Iterator, Tuple, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """Represents a single PDF page."""
    page_number: int
    width: float
    height: float
    text: str
    images: List[bytes]
    is_scanned: bool = False

    def has_text(self) -> bool:
        """Check if page has extractable text."""
        return bool(self.text.strip())

    def has_images(self) -> bool:
        """Check if page contains images."""
        return len(self.images) > 0


@dataclass
class PDFInfo:
    """PDF file metadata."""
    path: Path
    total_pages: int
    title: Optional[str] = None
    author: Optional[str] = None
    is_encrypted: bool = False
    file_size_mb: float = 0.0

    @property
    def is_large_file(self) -> bool:
        """Check if this is a large file (>200MB)."""
        return self.file_size_mb > 200


class PDFReader:
    """
    Streaming PDF reader for large files.

    Features:
    - Page-by-page reading (doesn't load entire file)
    - Memory efficient
    - Detects scanned pages
    - Extracts images and text
    """

    def __init__(
        self,
        pdf_path: str | Path,
        dpi: int = 200,
        extract_images: bool = True
    ):
        """
        Initialize PDF Reader.

        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image extraction
            extract_images: Whether to extract images from pages
        """
        self.pdf_path = Path(pdf_path)
        self.dpi = dpi
        self.extract_images = extract_images
        self._doc: Optional[fitz.Document] = None

    def open(self) -> "PDFReader":
        """Open the PDF file."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        try:
            self._doc = fitz.open(str(self.pdf_path))
            logger.info(f"Opened PDF: {self.pdf_path.name}")
            return self
        except Exception as e:
            raise IOError(f"Failed to open PDF: {e}")

    def close(self) -> None:
        """Close the PDF file."""
        if self._doc:
            self._doc.close()
            self._doc = None
            logger.info(f"Closed PDF: {self.pdf_path.name}")

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_info(self) -> PDFInfo:
        """Get PDF metadata."""
        if not self._doc:
            raise RuntimeError("PDF not opened. Call open() first.")

        file_size_mb = self.pdf_path.stat().st_size / 1024 / 1024

        metadata = self._doc.metadata
        return PDFInfo(
            path=self.pdf_path,
            total_pages=len(self._doc),
            title=metadata.get("title"),
            author=metadata.get("author"),
            is_encrypted=self._doc.is_encrypted,
            file_size_mb=file_size_mb
        )

    def iter_pages(
        self,
        start: int = 0,
        end: Optional[int] = None,
        extract_text: bool = True,
        extract_images: bool = None
    ) -> Iterator[PDFPage]:
        """
        Iterate over PDF pages.

        Args:
            start: Starting page number (0-indexed)
            end: Ending page number (exclusive), None for all pages
            extract_text: Whether to extract text from pages
            extract_images: Whether to extract images, overrides instance default

        Yields:
            PDFPage objects
        """
        if not self._doc:
            raise RuntimeError("PDF not opened. Call open() first.")

        if extract_images is None:
            extract_images = self.extract_images

        end = end or len(self._doc)
        total = len(self._doc)

        for page_num in range(start, min(end, total)):
            try:
                page = self._doc.load_page(page_num)
                page_rect = page.rect

                # Extract text
                text = ""
                if extract_text:
                    text = page.get_text()

                # Extract images
                images = []
                if extract_images:
                    images = self._extract_page_images(page)

                # Determine if page is scanned (little text, likely image-based)
                is_scanned = self._is_scanned_page(text, images)

                yield PDFPage(
                    page_number=page_num,
                    width=page_rect.width,
                    height=page_rect.height,
                    text=text,
                    images=images,
                    is_scanned=is_scanned
                )

                # Explicit cleanup
                del page

            except Exception as e:
                logger.error(f"Error reading page {page_num}: {e}")
                # Continue with next page
                continue

    def read_page(self, page_number: int) -> Optional[PDFPage]:
        """
        Read a single page.

        Args:
            page_number: Page number (0-indexed)

        Returns:
            PDFPage object or None if error
        """
        try:
            for page in self.iter_pages(start=page_number, end=page_number + 1):
                return page
        except Exception as e:
            logger.error(f"Failed to read page {page_number}: {e}")
            return None

    def read_page_chunk(
        self,
        start: int,
        size: int
    ) -> List[PDFPage]:
        """
        Read a chunk of pages.

        Args:
            start: Starting page number (0-indexed)
            size: Number of pages to read

        Returns:
            List of PDFPage objects
        """
        pages = []
        for page in self.iter_pages(start=start, end=start + size):
            pages.append(page)
        return pages

    def _extract_page_images(self, page: fitz.Page) -> List[bytes]:
        """Extract images from a page."""
        images = []

        try:
            # Get image references
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = self._doc.extract_image(xref)

                    if base_image:
                        image_bytes = base_image["image"]
                        images.append(image_bytes)

                except Exception as e:
                    logger.debug(f"Failed to extract image {img_index}: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Error extracting images: {e}")

        return images

    def _is_scanned_page(self, text: str, images: List[bytes]) -> bool:
        """
        Determine if a page is scanned (image-based).

        A page is considered scanned if:
        - It has very little text (< 50 chars)
        - It contains images
        """
        text_chars = len(text.strip())
        has_images = len(images) > 0

        # Also check if page renders as an image (full page scan)
        # This is a simple heuristic - real detection would need OCR check
        return text_chars < 50 and has_images

    def get_page_image(self, page_number: int) -> Optional[bytes]:
        """
        Render a page as an image (for scanned pages).

        Args:
            page_number: Page number (0-indexed)

        Returns:
            Image bytes in PNG format
        """
        if not self._doc:
            raise RuntimeError("PDF not opened. Call open() first.")

        try:
            page = self._doc.load_page(page_number)

            # Render page to pixmap
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")

            # Cleanup
            pix = None
            del page

            return img_bytes

        except Exception as e:
            logger.error(f"Failed to render page {page_number}: {e}")
            return None

    def get_page_range_text(self, start: int, end: int) -> str:
        """
        Get combined text from a range of pages.

        Args:
            start: Start page (0-indexed, inclusive)
            end: End page (0-indexed, exclusive)

        Returns:
            Combined text from all pages
        """
        text_parts = []
        for page in self.iter_pages(start=start, end=end, extract_images=False):
            text_parts.append(page.text)
        return "\n\n".join(text_parts)
