#!/usr/bin/env python3
"""Test batch processing fixes."""

import sys

def test_imports():
    """Test all imports for batch processing."""
    print("Testing imports...")
    
    try:
        from src.core.memory_manager import MemoryManager
        print("[OK] MemoryManager")
        
        from src.batch.batch_processor import BatchProcessor
        print("[OK] BatchProcessor")
        
        from src.batch.task_queue import TaskQueue
        print("[OK] TaskQueue")
        
        from src.core.converter import DoclingConverter
        print("[OK] DoclingConverter")
        
        from src.utils.logger import ProgressLogger
        print("[OK] ProgressLogger")
        
        return True
    except Exception as e:
        print(f"[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_manager():
    """Test MemoryManager methods."""
    print("\nTesting MemoryManager...")
    
    try:
        from src.core.memory_manager import MemoryManager
        
        mm = MemoryManager()
        
        # Test all methods
        stats = mm.get_stats()
        print(f"[OK] get_stats - Process: {stats.process_mb:.0f}MB, System: {stats.percent:.0f}%")
        
        pressure = mm.get_memory_pressure()
        print(f"[OK] get_memory_pressure - {pressure}")
        
        is_ok = mm.check_memory()
        print(f"[OK] check_memory - {is_ok}")
        
        chunk = mm.recommend_chunk_size()
        print(f"[OK] recommend_chunk_size - {chunk}")
        
        return True
    except Exception as e:
        print(f"[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_processor_memory_logic():
    """Test the memory checking logic used in batch_processor."""
    print("\nTesting batch processor memory logic...")
    
    try:
        from src.core.memory_manager import MemoryManager
        
        # Simulate the logic from batch_processor.py
        mem_manager = MemoryManager()
        pressure = mem_manager.get_memory_pressure()
        
        # Test worker adjustment logic
        max_workers = 2
        if pressure == "critical":
            actual_workers = 1
            print(f"[OK] Critical pressure - workers: {max_workers} -> {actual_workers}")
        elif pressure == "high":
            actual_workers = max(1, max_workers // 2)
            print(f"[OK] High pressure - workers: {max_workers} -> {actual_workers}")
        else:
            actual_workers = max_workers
            print(f"[OK] {pressure.title()} pressure - workers: {max_workers}")
        
        return True
    except Exception as e:
        print(f"[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("BATCH PROCESSING FIXES TEST")
    print("=" * 60)
    
    results = []
    results.append(test_imports())
    results.append(test_memory_manager())
    results.append(test_batch_processor_memory_logic())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n[SUCCESS] All batch processing tests passed!")
        print("\nYou can now run:")
        print("  python pdf2md.py batch ./pdfs --workers 1")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
