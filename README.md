# PDF2MD

**A high-precision PDF to Markdown converter optimized for large scanned PDF files and AMD platforms.**

**Version**: 1.1.1 (2025-01-13)
**Status**: Stable ✅

---

## ✨ What's New in v1.1.1

### 🎯 Critical Fix: Progress Bar Visibility

**Problem**: Progress bar was not visible during batch conversion (appeared stuck at "0/30")

**Root Cause**: Docling/RapidOCR INFO log output overwhelmed the Rich progress bar display

**Solution**: Temporarily reduce log level to WARNING during batch processing

**Result**: ✅ Progress bar now clearly shows conversion progress from 0% to 100%

### Test Results

Before fix:
```
[大量 INFO 日志]
⠋ Converting PDFs... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% 0/30
```

After fix:
```
✓ 完成: 文件1.pdf
✓ 完成: 文件2.pdf
  Converting PDFs... ████████────────────────────────────────  20% 6/30
```

---

## ✨ Features

- **⚡ GPU Acceleration** - Auto-detects and uses AMD/NVIDIA/Apple GPUs for 4x speedup
- **💾 Memory-efficient processing** - Handles large PDFs (>200MB) with streaming/chunked processing
- **🔍 Advanced OCR** - Converts scanned PDFs using Docling's advanced OCR (RapidOCR)
- **🚀 Batch processing** - Convert multiple files in parallel with **visible progress bar** ✨
- **🖼️ Image extraction** - Extracts images to separate folders
- **📐 Formula handling** - LaTeX formulas saved as images
- **📊 Progress tracking** - Real-time progress display (FIXED in v1.1.1)
- **🎯 Platform optimized** - Specialized optimizations for AMD AI MAX+ 395/8060S
- **🌏 Chinese filename support** - Full UTF-8 support for Chinese and mixed-language filenames
- **✅ Clean output** - Progress bar not overwhelmed by log messages (v1.1.1)

---

## 🎯 Performance

| Platform | 899页PDF处理时间 | 相对提升 |
|----------|----------------|----------|
| Intel Ultra9 (原系统) | 60 分钟 | 1.0x (baseline) |
| AMD CPU优化 | 30 分钟 | 2.0x |
| **AMD GPU加速** | **15 分钟** | **4.0x** |

> **更多性能信息**: 查看 [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)

---

## 📋 Requirements

- **Python**: 3.10 or higher
- **OS**: Windows 10/11 (primary), Linux/Mac supported
- **Memory**: 16GB+ RAM recommended, 128GB optimal
- **GPU**: Optional (AMD ROCm, NVIDIA CUDA, or Apple MPS)

---

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

```bash
# For AMD GPUs (ROCm)
pip install torch --index-url https://download.pytorch.org/whl/rocm

# For NVIDIA GPUs (CUDA)
pip install torch

# For CPU-only
pip install torch
```

### 4. Verify installation:

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## 🚀 Quick Start

### Convert a single PDF:

```bash
python pdf2md.py convert document.pdf
```

### Batch convert directory (with visible progress bar):

```bash
python pdf2md.py batch ./pdfs --workers 12
```

**Expected output (v1.1.1)**:
```
Found 30 PDF file(s) to convert
✓ 完成: 文件1.pdf
✓ 完成: 文件2.pdf
  Converting PDFs... ████████────────────────────────────────  20% 6/30
✓ 完成: 文件3.pdf
  Converting PDFs... ████████████████────────────────────────  40% 12/30
...
╔══════════════════════════════════════════════════════════════╗
║                 Batch Conversion Complete                     ║
╠══════════════════════════════════════════════════════════════╣
║ Total: 30                                                     ║
║ Successful: 30                                                ║
║ Failed: 0                                                     ║
╚══════════════════════════════════════════════════════════════╝
```

### Run performance benchmark:

```bash
python benchmark.py report.pdf
```

---

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

### `batch` - Convert all PDFs in a directory

```bash
python pdf2md.py batch [OPTIONS] DIRECTORY
```

**Options:**
- `-o, --output DIR` - Output directory
- `--pattern GLOB` - File pattern (default: *.pdf)
- `-r, --recursive` - Search subdirectories
- `-w, --workers INT` - Parallel workers (default: auto-detect)

### `info` - Show system information

```bash
python pdf2md.py info
```

---

## 🧪 Testing

### Test Scripts Included

Four comprehensive test scripts verify the progress bar fix:

1. **test_progress_real.py** - Basic progress bar behavior test
2. **test_batch_simulation.py** - Batch processing simulation
3. **test_real_batch.py** - Log interference comparison test
4. **test_actual_batch.py** - Actual batch processing test

### Running Tests

```bash
# Quick progress bar test
python test_progress_real.py

# Log interference comparison (shows before/after fix)
python test_real_batch.py

# Actual batch processing with real PDFs
python test_actual_batch.py
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize defaults:

```yaml
# Conversion settings
conversion:
  ocr_enabled: true
  ocr_languages: ["en", "zh-CN", "zh-TW"]

# Memory management
memory:
  max_pages_in_memory: 20
  process_chunk_size: 15

# Processing settings
processing:
  max_workers: 12
  dpi: 200

# Performance optimization
performance:
  enable_gpu: true
  accelerator_device: "auto"
  ocr_batch_size: 64
```

---

## 💡 Performance Tips

### 1. Enable GPU acceleration

```bash
# Auto-detect GPU (recommended)
python pdf2md.py convert doc.pdf
```

### 2. Optimize batch size for your GPU

| GPU Memory | Recommended batch_size |
|------------|----------------------|
| <4GB       | 8-16                 |
| 4-8GB      | 16-32                |
| 8-16GB     | 32-64                |
| >16GB      | 64-128               |

### 3. Use optimal worker count

```bash
# Auto-detect (recommended)
python pdf2md.py batch ./pdfs

# Manually specify
python pdf2md.py batch ./pdfs --workers 16
```

---

## 🐛 Troubleshooting

### "Docling is not installed"
```bash
pip install docling[ocr]
```

### "GPU not detected"

```bash
# 1. Verify PyTorch installation
python -c "import torch; print(torch.cuda.is_available())"

# 2. Reinstall PyTorch
pip install --upgrade torch
```

### Progress bar not visible

**Status**: ✅ Fixed in v1.1.1

If you still don't see the progress bar clearly:

1. Verify you have v1.1.1 or later:
```bash
type VERSION
```

2. Run the test to verify:
```bash
python test_real_batch.py
```

---

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history (v1.1.0, v1.1.1)
- **[FINAL_REPORT.md](FINAL_REPORT.md)** - Complete release report (v1.1.1)
- **[PROGRESS_BAR_FIX_REPORT.md](PROGRESS_BAR_FIX_REPORT.md)** - Progress bar fix details
- **[QUICKSTART_AMD.md](QUICKSTART_AMD.md)** - 5-minute quick start guide
- **[PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)** - Performance optimization guide

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

---

## 📄 License

MIT License

---

## 🗺️ Roadmap

### Completed ✅
- [x] GPU acceleration (AMD ROCm, NVIDIA CUDA, Apple MPS)
- [x] Automatic hardware detection
- [x] Performance optimization for AMD AI MAX+ 395
- [x] Intelligent memory management
- [x] Benchmarking tool
- [x] Chinese filename support (v1.1.0)
- [x] Progress bar visibility fix (v1.1.1)
- [x] Clean console output (v1.1.1)

### In Progress 🚧
- [ ] Multi-process batch processing
- [ ] VLM pipeline integration
- [ ] Resume interrupted conversions

### Planned 📋
- [ ] GUI version (PyQt6)
- [ ] Output to HTML/JSON formats
- [ ] Distributed processing
- [ ] NPU integration

---

**Version**: 1.1.1 (2025-01-13)
**Status**: Stable ✅
**Test Coverage**: ✅ All tests passing
**Package**: PDF2MD_v1.1.1.zip
