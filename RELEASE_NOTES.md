# PDF2MD v1.1.0 Release Notes

**Release Date**: 2025-01-13
**Status**: Stable ✅

## 📦 Package Information

- **Filename**: `PDF2MD_v1.1.0.zip`
- **Size**: ~387 KB
- **Format**: ZIP archive
- **Platform**: Windows 10/11, Linux, macOS

## 🎯 What's New in v1.1.0

### Key Fixes

1. **Progress Bar Not Updating** ✅
   - Fixed callback function to properly update Rich progress bar
   - Progress now correctly shows completion status (e.g., "15/30")
   - No more stuck at "0/30" during batch conversion

2. **Unicode Encoding Errors** ✅
   - Added full UTF-8 console support for Windows
   - Fixed Chinese filename handling in batch operations
   - Replaced error-prone Unicode symbols with ASCII equivalents

3. **WMIC Error Messages** ✅
   - Suppressed annoying "wmic is not recognized" warnings
   - Silent system detection on Windows 11
   - Cleaner console output

### Enhancements

- **Chinese Filename Support**: Full UTF-8 support for Chinese and mixed-language filenames
- **Better Error Messages**: Improved encoding for error display
- **Test Suite**: Comprehensive test script (`test_batch_fix.py`) for validation

### Technical Changes

**Modified Files**:
- `src/cli.py`: Fixed progress callback and UTF-8 encoding
- `src/utils/system_detector.py`: Added stderr suppression for wmic
- `src/core/converter.py`: Added stderr suppression for wmic
- `test_batch_fix.py`: Complete rewrite with encoding fixes

**New Files**:
- `CHANGELOG.md`: Version history documentation
- `BATCH_FIX_REPORT.md`: Detailed bug fix report
- `VERSION`: Current version indicator (1.1.0)

## ✅ Testing

All tests pass successfully:

```
✓ Progress bar test: OK
✓ Chinese filename test: OK
✓ Task queue test: OK
```

**Total**: 3/3 tests passing

## 📋 Installation

### Quick Install

1. Extract `PDF2MD_v1.1.0.zip`
2. Open terminal/command prompt in the extracted directory
3. Install dependencies:

```bash
pip install -r requirements.txt
pip install docling[ocr]
```

4. Verify installation:

```bash
python test_batch_fix.py
```

### Running the Application

```bash
# Convert a single PDF
python pdf2md.py convert document.pdf

# Batch convert directory
python pdf2md.py batch ./pdfs --workers 8

# Show system info
python pdf2md.py info
```

## 🐛 Known Issues

- **RapidOCR Warnings**: "RapidOCR returned empty result!" warnings may appear for PDF pages without text content. This is normal and not an error.
- **WMIC Deprecation**: The deprecated `wmic` command is now silently suppressed on Windows 11. System detection uses alternative methods.

## 📚 Documentation

- **[README.md](README.md)** - Main documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[BATCH_FIX_REPORT.md](BATCH_FIX_REPORT.md)** - Bug fix details
- **[QUICKSTART_AMD.md](QUICKSTART_AMD.md)** - Quick start guide
- **[PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)** - Performance tuning

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
# Conversion settings
conversion:
  ocr_enabled: true
  ocr_languages: ["en", "zh-CN", "zh-TW"]

# Processing settings
processing:
  max_workers: 12
  dpi: 200

# Performance settings
performance:
  enable_gpu: true
  ocr_batch_size: 64
```

## 🚀 Performance

| Platform | File Size | Pages | Time | Speed |
|----------|-----------|-------|------|-------|
| AMD AI MAX+ 395 | 184 MB | 899 | ~15 min | 60 pages/min |
| AMD CPU (32-core) | 184 MB | 899 | ~30 min | 30 pages/min |
| Intel Ultra9 | 184 MB | 899 | ~60 min | 15 pages/min |

## 🤝 Support

For issues, questions, or contributions:

1. Check the [BATCH_FIX_REPORT.md](BATCH_FIX_REPORT.md) for known issues
2. Review the [CHANGELOG.md](CHANGELOG.md) for version history
3. Run `python test_batch_fix.py` to verify installation
4. Check logs in `pdf2md.log` for detailed error information

## 📄 License

MIT License - See LICENSE file for details

---

**Previous Version**: [v1.0.0](#v100---2025-01-13)
**Next Version**: v1.2.0 (Planned)
