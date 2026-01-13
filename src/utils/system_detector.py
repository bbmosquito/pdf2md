"""
System Detector for hardware-aware optimization.

Detects CPU, GPU, and memory capabilities to optimize performance.
"""

import os
import platform
import psutil
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CPUInfo:
    """CPU information."""
    model: str
    cores_physical: int
    cores_total: int
    frequency_mhz: Optional[float]
    architecture: str


@dataclass
class GPUInfo:
    """GPU information."""
    vendor: str  # 'nvidia', 'amd', 'intel', 'apple', 'none'
    model: str
    memory_mb: Optional[int]
    compute_capability: Optional[str]
    supports_cuda: bool
    supports_rocm: bool
    supports_mps: bool  # Apple Metal Performance Shaders


@dataclass
class MemoryInfo:
    """Memory information."""
    total_mb: float
    available_mb: float
    is_large_system: bool  # >64GB


@dataclass
class SystemCapabilities:
    """Complete system capabilities."""
    cpu: CPUInfo
    gpu: GPUInfo
    memory: MemoryInfo
    platform: str
    python_version: str

    def get_optimal_workers(self) -> int:
        """Get optimal number of workers for this system."""
        # Use physical cores as baseline
        workers = self.cpu.cores_physical

        # Memory-based adjustment for 32GB systems
        total_mem_gb = self.memory.total_mb / 1024
        if total_mem_gb >= 64:
            # Large memory systems (>=64GB)
            workers = int(workers * 1.5)
        elif total_mem_gb >= 32:
            # Medium memory systems (32-64GB) - optimal for AMD AI MAX+ 395
            workers = int(workers * 1.0)  # Keep baseline
        elif total_mem_gb >= 16:
            # Small memory systems (16-32GB)
            workers = int(workers * 0.75)
        else:
            # Very small memory (<16GB)
            workers = int(workers * 0.5)

        # GPU adjustment (only if we have enough CPU memory)
        if self.gpu.vendor != 'none' and total_mem_gb >= 32:
            workers = int(workers * 1.0)  # Moderate increase for 32GB systems
        elif self.gpu.vendor != 'none':
            workers = int(workers * 1.2)  # Larger increase for bigger systems

        # Cap at reasonable values
        return max(1, min(workers, 16))  # Cap at 16 for 32GB systems

    def get_optimal_batch_size(self) -> int:
        """Get optimal batch size for OCR/layout processing."""
        # Default batch sizes
        base_batch = 16

        # Scale based on GPU memory
        if self.gpu.supports_cuda or self.gpu.supports_rocm:
            # GPU can handle larger batches
            if self.gpu.memory_mb and self.gpu.memory_mb >= 64000:  # >=64GB (e.g., 96GB)
                return 128  # Super large batches for 96GB VRAM
            elif self.gpu.memory_mb and self.gpu.memory_mb >= 16000:  # >=16GB
                return 64   # Large batches
            elif self.gpu.memory_mb and self.gpu.memory_mb >= 8000:  # >=8GB
                return 32   # Medium batches
            else:
                return 16   # Default GPU batch size
        elif self.gpu.vendor == 'apple' and self.gpu.supports_mps:
            if self.gpu.memory_mb and self.gpu.memory_mb >= 16000:
                return 32
            else:
                return 16
        else:
            # CPU-only processing
            if self.cpu.cores_physical >= 16:
                return 16
            elif self.cpu.cores_physical >= 8:
                return 8
            else:
                return 4

    def get_recommended_chunk_size(self) -> int:
        """Get recommended PDF page chunk size."""
        total_mem_gb = self.memory.total_mb / 1024

        # Chunk size based on available memory
        if total_mem_gb >= 64:
            # Large memory systems (>=64GB)
            return 20
        elif total_mem_gb >= 32:
            # Medium memory systems (32-64GB) - optimal for AMD AI MAX+ 395 with 32GB RAM
            return 10
        elif total_mem_gb >= 16:
            # Small memory systems (16-32GB)
            return 5
        else:
            # Very small memory (<16GB)
            return 3


class SystemDetector:
    """
    Detects system hardware and capabilities.

    Automatically detects:
    - CPU cores and frequency
    - GPU vendor and capabilities (CUDA/ROCm/MPS)
    - Memory size
    - Platform specifics
    """

    def __init__(self):
        self._cpu_info: Optional[CPUInfo] = None
        self._gpu_info: Optional[GPUInfo] = None
        self._memory_info: Optional[MemoryInfo] = None
        self._capabilities: Optional[SystemCapabilities] = None

    def detect(self) -> SystemCapabilities:
        """
        Detect all system capabilities.

        Returns:
            SystemCapabilities with complete system information
        """
        if self._capabilities is None:
            self._cpu_info = self._detect_cpu()
            self._gpu_info = self._detect_gpu()
            self._memory_info = self._detect_memory()

            self._capabilities = SystemCapabilities(
                cpu=self._cpu_info,
                gpu=self._gpu_info,
                memory=self._memory_info,
                platform=platform.system(),
                python_version=platform.python_version()
            )

            logger.info(f"Detected system: {self._capabilities}")

        return self._capabilities

    def _detect_cpu(self) -> CPUInfo:
        """Detect CPU information."""
        # Get CPU info
        physical_cores = psutil.cpu_count(logical=False) or 1
        total_cores = psutil.cpu_count(logical=True) or 1

        # Try to get CPU frequency
        freq = None
        try:
            freq_info = psutil.cpu_freq()
            if freq_info:
                freq = freq_info.max
        except Exception as e:
            logger.debug(f"Could not get CPU frequency: {e}")

        # Try to detect CPU model
        model = "Unknown CPU"
        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            model = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
        elif platform.system() == "Windows":
            try:
                import subprocess
                result = subprocess.check_output(
                    "wmic cpu get name",
                    shell=True,
                    text=True
                )
                lines = result.strip().split('\n')
                if len(lines) > 1:
                    model = lines[1].strip()
            except Exception:
                pass
        elif platform.system() == "Darwin":
            try:
                import subprocess
                result = subprocess.check_output(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    text=True
                )
                model = result.strip()
            except Exception:
                pass

        # Detect AMD CPU specifically
        cpu_arch = platform.machine() or "unknown"
        if "AMD" in model or "amd" in model:
            # AMD CPU detected
            if "395" in model or "AI MAX" in model:
                model = f"AMD AI MAX+ 395 (Detected)"
            elif "Ryzen" in model:
                # Keep original Ryzen name
                pass

        return CPUInfo(
            model=model,
            cores_physical=physical_cores,
            cores_total=total_cores,
            frequency_mhz=freq,
            architecture=cpu_arch
        )

    def _detect_gpu(self) -> GPUInfo:
        """Detect GPU information."""
        vendor = "none"
        model = "No GPU detected"
        memory_mb = None
        compute_capability = None
        supports_cuda = False
        supports_rocm = False
        supports_mps = False

        # Check for NVIDIA GPU
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(',')
                    if len(parts) >= 2:
                        model = parts[0].strip()
                        mem_str = parts[1].strip()
                        # Parse memory like "8192 MiB"
                        mem_mb = int(mem_str.split()[0])
                        memory_mb = mem_mb
                        vendor = "nvidia"
                        supports_cuda = True
                        logger.info(f"Detected NVIDIA GPU: {model} with {memory_mb}MB")
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"No NVIDIA GPU detected: {e}")

        # Check for AMD GPU
        if vendor == "none":
            try:
                # Try AMD GPU query on Windows
                if platform.system() == "Windows":
                    try:
                        import subprocess
                        result = subprocess.run(
                            ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            output = result.stdout
                            if "AMD" in output or "Radeon" in output or "Advanced Micro Devices" in output:
                                # Parse AMD GPU info
                                lines = [line.strip() for line in output.split('\n') if line.strip()]
                                if len(lines) > 1:
                                    model = lines[1].split()[0] if lines[1] else "AMD GPU"
                                    vendor = "amd"
                                    supports_rocm = True
                                    logger.info(f"Detected AMD GPU: {model}")
                    except Exception as e:
                        logger.debug(f"AMD GPU detection failed: {e}")
            except Exception as e:
                logger.debug(f"AMD GPU detection error: {e}")

        # Additional AMD GPU detection via PyTorch
        if vendor == "none":
            try:
                import torch
                if torch.cuda.is_available():
                    # Check if it's ROCm
                    if hasattr(torch.version, 'cuda') and 'rocm' in torch.version.cuda.lower():
                        vendor = "amd"
                        model = "AMD GPU (via ROCm/PyTorch)"
                        supports_rocm = True
                        memory_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                        logger.info(f"Detected AMD GPU via PyTorch ROCm: {model} with {memory_mb:.0f}MB")
                    else:
                        # CUDA (likely NVIDIA)
                        vendor = "nvidia"
                        supports_cuda = True
                        memory_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                        model = torch.cuda.get_device_name(0)
                        logger.info(f"Detected CUDA GPU: {model} with {memory_mb:.0f}MB")
            except ImportError:
                logger.debug("PyTorch not available for GPU detection")
            except Exception as e:
                logger.debug(f"PyTorch GPU detection failed: {e}")

        # Check for Apple Silicon (M1/M2/M3)
        if vendor == "none" and platform.system() == "Darwin":
            try:
                import subprocess
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Apple" in result.stdout:
                    vendor = "apple"
                    model = result.stdout.strip()
                    supports_mps = True
                    logger.info(f"Detected Apple Silicon: {model}")
            except Exception:
                pass

        # Special detection for AMD AI MAX+ 395
        if vendor == "amd" or vendor == "none":
            # Check for AMD AI MAX specifically
            if platform.system() == "Windows":
                try:
                    import subprocess
                    result = subprocess.check_output(
                        "wmic cpu get name",
                        shell=True,
                        text=True
                    )
                    if "395" in result or "AI MAX" in result:
                        vendor = "amd"
                        model = "AMD AI MAX+ 395 / 8060S"
                        supports_rocm = True
                        # Assume large GPU memory for this platform
                        memory_mb = 96000  # Up to 96GB
                        logger.info(f"Detected AMD AI MAX+ 395 platform with {memory_mb}MB GPU memory")
                except Exception:
                    pass

        return GPUInfo(
            vendor=vendor,
            model=model,
            memory_mb=memory_mb,
            compute_capability=compute_capability,
            supports_cuda=supports_cuda,
            supports_rocm=supports_rocm,
            supports_mps=supports_mps
        )

    def _detect_memory(self) -> MemoryInfo:
        """Detect system memory information."""
        mem = psutil.virtual_memory()

        total_mb = mem.total / (1024 * 1024)
        available_mb = mem.available / (1024 * 1024)
        is_large = total_mb >= 64 * 1024  # >=64GB

        return MemoryInfo(
            total_mb=total_mb,
            available_mb=available_mb,
            is_large_system=is_large
        )

    def get_recommended_accelerator_device(self) -> str:
        """
        Get recommended accelerator device for Docling.

        Returns:
            'cuda', 'mps', or 'cpu'
        """
        caps = self.detect()

        if caps.gpu.supports_cuda or caps.gpu.supports_rocm:
            return "cuda"
        elif caps.gpu.supports_mps:
            return "mps"
        else:
            return "cpu"

    def print_system_info(self):
        """Print detailed system information to logs."""
        caps = self.detect()

        logger.info("=" * 60)
        logger.info("System Detection Results")
        logger.info("=" * 60)
        logger.info(f"Platform: {caps.platform}")
        logger.info(f"Python: {caps.python_version}")
        logger.info("")
        logger.info(f"CPU: {caps.cpu.model}")
        logger.info(f"  Physical Cores: {caps.cpu.cores_physical}")
        logger.info(f"  Logical Cores: {caps.cpu.cores_total}")
        if caps.cpu.frequency_mhz:
            logger.info(f"  Max Frequency: {caps.cpu.frequency_mhz:.0f} MHz")
        logger.info("")
        logger.info(f"GPU: {caps.gpu.model}")
        logger.info(f"  Vendor: {caps.gpu.vendor}")
        if caps.gpu.memory_mb:
            logger.info(f"  Memory: {caps.gpu.memory_mb:.0f} MB ({caps.gpu.memory_mb/1024:.1f} GB)")
        logger.info(f"  CUDA Support: {caps.gpu.supports_cuda}")
        logger.info(f"  ROCm Support: {caps.gpu.supports_rocm}")
        logger.info(f"  MPS Support: {caps.gpu.supports_mps}")
        logger.info("")
        logger.info(f"Memory: {caps.memory.total_mb/1024:.1f} GB")
        logger.info(f"  Available: {caps.memory.available_mb/1024:.1f} GB")
        logger.info(f"  Large System: {caps.memory.is_large_system}")
        logger.info("")
        logger.info("Recommended Settings:")
        logger.info(f"  Optimal Workers: {caps.get_optimal_workers()}")
        logger.info(f"  Optimal Batch Size: {caps.get_optimal_batch_size()}")
        logger.info(f"  Chunk Size: {caps.get_recommended_chunk_size()}")
        logger.info(f"  Accelerator Device: {self.get_recommended_accelerator_device()}")
        logger.info("=" * 60)


# Global instance
_detector = None


def get_system_detector() -> SystemDetector:
    """Get the global system detector instance."""
    global _detector
    if _detector is None:
        _detector = SystemDetector()
    return _detector


def detect_system() -> SystemCapabilities:
    """Convenience function to detect system capabilities."""
    return get_system_detector().detect()
