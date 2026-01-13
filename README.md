# PDF2MD

**A high-precision PDF to Markdown converter optimized for large scanned PDF files and AMD platforms.**

## ✨ Features

- **⚡ GPU Acceleration** - Auto-detects and uses AMD/NVIDIA/Apple GPUs for 4x speedup
- **💾 Memory-efficient processing** - Handles large PDFs (>200MB) with streaming/chunked processing
- **🔍 Advanced OCR** - Converts scanned PDFs using Docling's advanced OCR (RapidOCR)
- **🚀 Batch processing** - Convert multiple files in parallel with optimal worker count
- **🖼️ Image extraction** - Extracts images to separate folders
- **📐 Formula handling** - LaTeX formulas saved as images
- **📊 Progress tracking** - Real-time progress display
- **🎯 Platform optimized** - Specialized optimizations for AMD AI MAX+ 395/8060S

## 🎯 Performance

| Platform | 899页PDF处理时间 | 相对提升 |
|----------|----------------|----------|
| Intel Ultra9 (原系统) | 60 分钟 | 1.0x (baseline) |
| AMD CPU优化 | 30 分钟 | 2.0x |
| **AMD GPU加速** | **15 分钟** | **4.0x** |

> **更多性能信息**: 查看 [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) 和 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)

## 📋 Requirements

- **Python**: 3.10 or higher
- **OS**: Windows 10/11 (primary), Linux/Mac supported
- **Memory**: 16GB+ RAM recommended, 128GB optimal
- **GPU**: Optional (AMD ROCm, NVIDIA CUDA, or Apple MPS)

## 🔧 Installation

## 🔧 Installation

### 1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Install Docling (required):

```bash
pip install docling[ocr]
```

### 3. Install PyTorch for GPU acceleration (optional but recommended):

#### For AMD GPUs (ROCm):

```bash
pip install torch --index-url https://download.pytorch.org/whl/rocm
```

#### For NVIDIA GPUs (CUDA):

```bash
pip install torch
```

#### For CPU-only:

```bash
pip install torch
```

### 4. Verify installation:

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 🚀 Quick Start

### Convert a single PDF (with auto GPU acceleration):

```bash
python pdf2md.py convert document.pdf
```

This creates:
```
document_md/
├── document.md
└── images/
    ├── image_0001.png
    ├── image_0002.png
    └── ...
```

### Convert with custom output:

```bash
python pdf2md.py convert document.pdf -o ./output
```

### Disable GPU acceleration (CPU-only):

```bash
python pdf2md.py convert document.pdf --no-gpu
```

### Batch convert directory with 12 workers:

```bash
python pdf2md.py batch ./pdfs --workers 12
```

### Convert multiple specific files:

```bash
python pdf2md.py multiple file1.pdf file2.pdf file3.pdf
```

### Run performance benchmark:

```bash
python benchmark.py report.pdf
```

## 📖 Command Reference

### `convert` - Convert a single PDF

```bash
python pdf2md.py convert [OPTIONS] PDF
```

**Options:**
- `-o, --output DIR` - Output directory
- `-w, --workers INT` - Number of parallel workers (default: auto-detect)
- `--ocr/--no-ocr` - Enable/disable OCR (default: enabled)
- `--dpi INT` - Image DPI for rendering (default: 200)
- `--gpu/--no-gpu` - Enable/disable GPU acceleration (default: auto-detect)
- `--device {auto,cuda,mps,cpu}` - Accelerator device (default: auto)
- `--batch-size INT` - OCR/Layout batch size (default: auto-detect)

**Examples:**
```bash
# Auto-detect optimal settings (recommended)
python pdf2md.py convert doc.pdf

# Force CPU mode
python pdf2md.py convert doc.pdf --no-gpu

# Custom batch size for large GPU memory
python pdf2md.py convert doc.pdf --batch-size 64

# High DPI for better quality
python pdf2md.py convert doc.pdf --dpi 300
```

### `batch` - Convert all PDFs in a directory

```bash
python pdf2md.py batch [OPTIONS] DIRECTORY
```

**Options:**
- `-o, --output DIR` - Output directory
- `--pattern GLOB` - File pattern (default: *.pdf)
- `-r, --recursive` - Search subdirectories
- `-w, --workers INT` - Parallel workers (default: auto-detect)
- `--ocr/--no-ocr` - Enable/disable OCR

### `multiple` - Convert specific files

```bash
python pdf2md.py multiple [OPTIONS] PDF1 [PDF2 ...]
```

### `info` - Show system information

```bash
python pdf2md.py info
```

### `benchmark` - Run performance benchmark (NEW)

```bash
python benchmark.py PDF [OPTIONS]
```

**Options:**
- `-o, --output FILE` - Save results to JSON file

**Examples:**
```bash
# Benchmark with test PDF
python benchmark.py report.pdf

# Save results
python benchmark.py report.pdf -o results.json
```

## ⚙️ Configuration

Edit `config.yaml` to customize defaults:

```yaml
# Conversion settings
conversion:
  output_format: markdown
  ocr_enabled: true
  ocr_languages: ["en", "zh-CN", "zh-TW"]

# Memory management (OPTIMIZED for large systems)
memory:
  max_pages_in_memory: 20  # Increased for 128GB systems
  process_chunk_size: 15   # Larger chunks for better throughput

# Processing settings
processing:
  max_workers: 12  # Optimized for AMD multi-core systems
  dpi: 200

# Performance optimization (GPU acceleration)
performance:
  enable_gpu: true           # Auto-detect and enable GPU
  accelerator_device: "auto" # Options: "auto", "cuda", "mps", "cpu"
  num_threads: null          # Auto-detect (physical core count)

  # Batch sizes for GPU processing
  ocr_batch_size: 64
  layout_batch_size: 64
  table_batch_size: 8

# Output settings
output:
  save_images: true
  image_format: png
  extract_formulas_as_images: true
```

**推荐配置**:
- **大内存系统** (>=64GB): 使用默认配置 (chunk_size=15, workers=12)
- **小内存系统** (<16GB): 降低 chunk_size=5, workers=4
- **GPU系统**: 使用 ocr_batch_size=64
- **CPU-only**: 使用 ocr_batch_size=16

## 📁 Project Structure

```
pdf2md/
├── pdf2md.py                    # Main entry point
├── benchmark.py                 # Performance benchmark tool (NEW)
├── config.yaml                  # Configuration file (OPTIMIZED)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── QUICKSTART_AMD.md            # 5-minute quick start guide (NEW)
├── PERFORMANCE_OPTIMIZATION.md  # Detailed optimization guide (NEW)
├── OPTIMIZATION_SUMMARY.md      # Optimization summary (NEW)
└── src/
    ├── cli.py                   # Command-line interface (ENHANCED)
    ├── core/
    │   ├── converter.py         # Core conversion engine (GPU ACCELERATED)
    │   ├── pdf_reader.py        # PDF reading utilities
    │   └── memory_manager.py    # Memory management (OPTIMIZED)
    ├── batch/
    │   ├── batch_processor.py   # Batch processing
    │   └── task_queue.py        # Task queue management
    └── utils/
        ├── system_detector.py   # Hardware detection (NEW)
        ├── logger.py            # Logging utilities
        └── config.py            # Configuration management
```

## 💡 Performance Tips

### 1. Enable GPU acceleration

GPU acceleration provides **2-3x** speedup:

```bash
# Auto-detect GPU (recommended)
python pdf2md.py convert doc.pdf

# Explicitly enable GPU
python pdf2md.py convert doc.pdf --gpu
```

### 2. Optimize batch size for your GPU

| GPU Memory | Recommended batch_size |
|------------|----------------------|
| <4GB       | 8-16                 |
| 4-8GB      | 16-32                |
| 8-16GB     | 32-64                |
| >16GB      | 64-128               |

```bash
python pdf2md.py convert doc.pdf --batch-size 64
```

### 3. Use optimal worker count

```bash
# Auto-detect (recommended)
python pdf2md.py convert doc.pdf

# Manually specify for your system
python pdf2md.py convert doc.pdf --workers 16
```

### 4. Run benchmarks to find optimal settings

```bash
python benchmark.py your_large_file.pdf
```

## 🐛 Troubleshooting

### "Docling is not installed"
```bash
pip install docling[ocr]
```

### "GPU not detected"

**Symptoms**: Log shows "No GPU detected, using CPU"

**Solutions**:
```bash
# 1. Verify PyTorch installation
python -c "import torch; print(torch.cuda.is_available())"

# 2. Reinstall PyTorch with ROCm (AMD)
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/rocm

# 3. Reinstall with CUDA (NVIDIA)
pip uninstall torch -y
pip install torch

# 4. Update Docling
pip install --upgrade docling
```

### "MemoryError" or system slowdown

**Solutions**:
```bash
# Reduce batch size
python pdf2md.py convert doc.pdf --batch-size 16

# Reduce workers
python pdf2md.py convert doc.pdf --workers 4

# Or edit config.yaml
# performance:
#   ocr_batch_size: 16
# processing:
#   max_workers: 4
```

### OCR quality issues

- Increase DPI: `--dpi 300`
- Check OCR language support in config.yaml
- Ensure PDF images are high resolution

### Slow performance on large files

**Check**:
1. Run `python benchmark.py your_file.pdf` to diagnose
2. Verify GPU acceleration is enabled in logs
3. Check Windows Task Manager → Performance → GPU

## 📚 Documentation

- **[QUICKSTART_AMD.md](QUICKSTART_AMD.md)** - 5-minute quick start guide
- **[PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)** - Detailed performance optimization guide (6000+ words)
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - Optimization work summary
- **[thinkall.md](thinkall.md)** - Original development documentation

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## 📄 License

MIT License

## 🗺️ Roadmap

### Completed ✅
- [x] GPU acceleration (AMD ROCm, NVIDIA CUDA, Apple MPS)
- [x] Automatic hardware detection
- [x] Performance optimization for AMD AI MAX+ 395
- [x] Intelligent memory management
- [x] Benchmarking tool

### In Progress 🚧
- [ ] Multi-process batch processing
- [ ] VLM pipeline integration
- [ ] Resume interrupted conversions

### Planned 📋
- [ ] GUI version (PyQt6)
- [ ] Output to HTML/JSON formats
- [ ] Distributed processing
- [ ] NPU integration
