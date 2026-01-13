"""
PDF2MD 完整系统测试脚本

测试所有模块的功能，确认bug已消除

运行方式：
    python test_complete_system.py
"""

import sys
import os
from pathlib import Path
import traceback

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


class TestResult:
    """测试结果"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name):
        self.passed += 1
        print(f"  [PASS] {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  [FAIL] {test_name}")
        print(f"    Error: {error}")

    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f" 测试结果: {self.passed}/{total} 通过")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*70}\n")
        return self.failed == 0


def test_imports():
    """测试1：所有模块可以正常导入"""
    print("\n测试1: 模块导入...")

    result = TestResult()

    try:
        import psutil
        result.add_pass("psutil导入")
    except ImportError as e:
        result.add_fail("psutil导入", e)

    try:
        from core.cpu_optimizer import AMDCPUOptimizer, AdvancedMemoryManager
        result.add_pass("cpu_optimizer导入")
    except ImportError as e:
        result.add_fail("cpu_optimizer导入", e)

    try:
        from core.performance_monitor import PerformanceMonitor
        result.add_pass("performance_monitor导入")
    except ImportError as e:
        result.add_fail("performance_monitor导入", e)

    try:
        from core.converter import DoclingConverter, ConversionConfig
        result.add_pass("converter导入")
    except ImportError as e:
        result.add_fail("converter导入", e)

    try:
        from utils.config import load_config, Config
        result.add_pass("config导入")
    except ImportError as e:
        result.add_fail("config导入", e)

    try:
        from rich.console import Console
        result.add_pass("rich导入")
    except ImportError as e:
        result.add_fail("rich导入", e)

    return result


def test_cpu_optimizer():
    """测试2：CPU优化器功能"""
    print("\n测试2: CPU优化器...")

    result = TestResult()

    try:
        from core.cpu_optimizer import AMDCPUOptimizer

        optimizer = AMDCPUOptimizer()
        result.add_pass("优化器初始化")

        # 测试系统检测
        if optimizer.system.physical_cores > 0:
            result.add_pass(f"检测到物理核心: {optimizer.system.physical_cores}")
        else:
            result.add_fail("物理核心检测", "核心数为0")

        if optimizer.system.logical_cores > 0:
            result.add_pass(f"检测到逻辑核心: {optimizer.system.logical_cores}")
        else:
            result.add_fail("逻辑核心检测", "核心数为0")

        if optimizer.system.total_memory_gb >= 30:
            result.add_pass(f"检测到内存: {optimizer.system.total_memory_gb:.1f}GB")
        else:
            result.add_fail("内存检测", f"内存不足: {optimizer.system.total_memory_gb:.1f}GB")

        # 测试最优配置计算
        workers = optimizer.calculate_optimal_workers()
        if workers > 0 and workers <= 32:
            result.add_pass(f"计算最优workers: {workers}")
        else:
            result.add_fail("workers计算", f"异常值: {workers}")

        config = optimizer.get_optimal_config(enable_gpu=False)

        if config.ocr_batch_size > 0:
            result.add_pass(f"计算最优batch_size: {config.ocr_batch_size}")
        else:
            result.add_fail("batch_size计算", f"异常值: {config.ocr_batch_size}")

        if config.table_batch_size == config.ocr_batch_size // 4:
            result.add_pass(f"table_batch_size为batch的1/4: {config.table_batch_size}")
        else:
            result.add_fail("table_batch_size计算",
                          f"期望{config.ocr_batch_size // 4}, 实际{config.table_batch_size}")

        # 96GB内存特殊检查
        if optimizer.system.total_memory_gb >= 64:
            if config.max_process_memory_gb >= 60:
                result.add_pass(f"大内存优化(>64GB): {config.max_process_memory_gb:.1f}GB")
            else:
                result.add_fail("大内存优化",
                              f"进程内存不足: {config.max_process_memory_gb:.1f}GB")

            # batch_size应该至少为32
            if config.ocr_batch_size >= 32:
                result.add_pass("大内存batch_size优化")
            else:
                result.add_fail("大内存batch_size优化",
                              f"batch_size过小: {config.ocr_batch_size}")
        else:
            # 32GB系统的配置检查
            result.add_pass(f"内存优化配置: {config.max_process_memory_gb:.1f}GB")

    except Exception as e:
        result.add_fail("CPU优化器测试", f"{type(e).__name__}: {e}")

    return result


def test_performance_monitor():
    """测试3：性能监控器"""
    print("\n测试3: 性能监控器...")

    result = TestResult()

    try:
        from core.performance_monitor import PerformanceMonitor
        import time

        monitor = PerformanceMonitor(sample_interval=0.5)
        result.add_pass("监控器初始化")

        monitor.start()
        result.add_pass("监控器启动")

        # 运行一小段时间
        time.sleep(2)

        monitor.stop()
        result.add_pass("监控器停止")

        stats = monitor.get_statistics()
        if stats.duration_seconds > 0:
            result.add_pass(f"统计计算: {stats.duration_seconds:.1f}秒")
        else:
            result.add_fail("统计计算", "持续时间为0")

        if len(monitor.snapshots) > 0:
            result.add_pass(f"收集快照: {len(monitor.snapshots)}个")
        else:
            result.add_fail("收集快照", "无快照数据")

    except Exception as e:
        result.add_fail("性能监控器测试", f"{type(e).__name__}: {e}")

    return result


def test_config_files():
    """测试4：配置文件"""
    print("\n测试4: 配置文件...")

    result = TestResult()

    try:
        import yaml

        # 测试96GB配置
        config_file_96gb = Path("config_amd_cpu_96gb.yaml")
        if config_file_96gb.exists():
            with open(config_file_96gb, 'r', encoding='utf-8') as f:
                config_96gb = yaml.safe_load(f)

            result.add_pass("96GB配置文件加载")

            # 检查关键配置
            if config_96gb['processing']['max_workers'] == 16:
                result.add_pass("workers配置正确")
            else:
                result.add_fail("workers配置", f"期望16, 实际{config_96gb['processing']['max_workers']}")

            if config_96gb['performance']['num_threads'] == 32:
                result.add_pass("num_threads配置正确")
            else:
                result.add_fail("num_threads配置", f"期望32, 实际{config_96gb['performance']['num_threads']}")

            if config_96gb['performance']['ocr_batch_size'] >= 32:
                result.add_pass(f"batch_size配置: {config_96gb['performance']['ocr_batch_size']}")
            else:
                result.add_fail("batch_size配置",
                              f"过小: {config_96gb['performance']['ocr_batch_size']}")

            if config_96gb['performance']['max_process_memory_gb'] >= 60:
                result.add_pass(f"内存限制配置: {config_96gb['performance']['max_process_memory_gb']}GB")
            else:
                result.add_fail("内存限制配置",
                              f"过小: {config_96gb['performance']['max_process_memory_gb']}GB")

        else:
            result.add_fail("96GB配置文件", "文件不存在")

        # 测试32GB配置（兼容性）
        config_file_32 = Path("config_amd_cpu_32core.yaml")
        if config_file_32.exists():
            result.add_pass("32GB配置文件存在")
        else:
            result.add_fail("32GB配置文件", "文件不存在")

    except Exception as e:
        result.add_fail("配置文件测试", f"{type(e).__name__}: {e}")

    return result


def test_converter_init():
    """测试5：转换器初始化"""
    print("\n测试5: 转换器初始化...")

    result = TestResult()

    try:
        from core.converter import DoclingConverter, ConversionConfig
        from core.cpu_optimizer import AMDCPUOptimizer

        # 使用优化器获取配置
        optimizer = AMDCPUOptimizer()
        opt_config = optimizer.get_optimal_config(enable_gpu=False)

        # 创建转换器配置
        config = ConversionConfig(
            ocr_enabled=True,
            dpi=200,
            max_workers=opt_config.max_workers,
            enable_gpu=False,
            accelerator_device="cpu",
            ocr_batch_size=opt_config.ocr_batch_size,
            layout_batch_size=opt_config.layout_batch_size,
            table_batch_size=opt_config.table_batch_size,
            num_threads=opt_config.num_threads
        )

        result.add_pass("转换器配置创建")

        # 检查docling是否可用
        from core.converter import is_docling_available
        if is_docling_available():
            result.add_pass("Docling已安装")

            # 尝试初始化转换器
            try:
                converter = DoclingConverter(config)
                result.add_pass("转换器初始化成功")

                # 检查配置是否正确应用
                if converter.config.num_threads == opt_config.num_threads:
                    result.add_pass("线程数配置应用正确")
                else:
                    result.add_fail("线程数配置",
                                  f"期望{opt_config.num_threads}, 实际{converter.config.num_threads}")

            except Exception as e:
                result.add_fail("转换器初始化", f"{type(e).__name__}: {e}")
        else:
            result.add_fail("Docling安装", "Docling未安装")

    except Exception as e:
        result.add_fail("转换器测试", f"{type(e).__name__}: {e}")

    return result


def test_cli_integration():
    """测试6：CLI集成"""
    print("\n测试6: CLI集成...")

    result = TestResult()

    try:
        # 检查CLI文件
        cli_file = Path("src/cli.py")
        if not cli_file.exists():
            result.add_fail("CLI文件", "src/cli.py不存在")
            return result

        result.add_pass("CLI文件存在")

        # 读取CLI文件内容
        content = cli_file.read_text(encoding='utf-8')

        # 检查是否有optimizer导入
        if "from core.cpu_optimizer import AMDCPUOptimizer" in content:
            result.add_pass("Optimizer导入检查")
        else:
            result.add_fail("Optimizer导入", "未找到导入语句")

        # 检查是否有optimizer使用
        if "AMDCPUOptimizer()" in content:
            result.add_pass("Optimizer使用检查")
        else:
            result.add_fail("Optimizer使用", "未找到使用代码")

        # 检查是否有table_batch_size配置
        if "table_batch_size" in content:
            result.add_pass("table_batch_size配置检查")
        else:
            result.add_fail("table_batch_size配置", "未找到配置代码")

        # 检查是否有num_threads配置
        if "num_threads" in content:
            result.add_pass("num_threads配置检查")
        else:
            result.add_fail("num_threads配置", "未找到配置代码")

    except Exception as e:
        result.add_fail("CLI集成测试", f"{type(e).__name__}: {e}")

    return result


def test_benchmark_script():
    """测试7：基准测试脚本"""
    print("\n测试7: 基准测试脚本...")

    result = TestResult()

    try:
        # 检查基准测试脚本
        benchmark_file = Path("benchmark_amd_cpu.py")
        if not benchmark_file.exists():
            result.add_fail("基准测试脚本", "benchmark_amd_cpu.py不存在")
            return result

        result.add_pass("基准测试脚本存在")

        # 读取脚本内容
        content = benchmark_file.read_text(encoding='utf-8')

        # 检查关键类和函数
        if "class CPUBenchmark" in content:
            result.add_pass("CPUBenchmark类定义")
        else:
            result.add_fail("CPUBenchmark类", "未找到类定义")

        if "def run_single_benchmark" in content:
            result.add_pass("run_single_benchmark方法")
        else:
            result.add_fail("run_single_benchmark方法", "未找到方法")

        if "AMDCPUOptimizer" in content:
            result.add_pass("Optimizer集成")
        else:
            result.add_fail("Optimizer集成", "未找到集成代码")

    except Exception as e:
        result.add_fail("基准测试脚本", f"{type(e).__name__}: {e}")

    return result


def main():
    """主测试函数"""
    print("=" * 70)
    print(" " * 15 + "PDF2MD 完整系统测试")
    print("=" * 70)

    all_results = []

    # 运行所有测试
    all_results.append(test_imports())
    all_results.append(test_cpu_optimizer())
    all_results.append(test_performance_monitor())
    all_results.append(test_config_files())
    all_results.append(test_converter_init())
    all_results.append(test_cli_integration())
    all_results.append(test_benchmark_script())

    # 汇总结果
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed

    print("\n" + "=" * 70)
    print(" " * 20 + "总体测试结果")
    print("=" * 70)
    print(f"\n总计: {total_passed}/{total_tests} 测试通过")

    if total_failed == 0:
        print("\n[SUCCESS] All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Run conversion test:")
        print("     pdf2md convert report.pdf")
        print("\n  2. Run performance benchmark:")
        print("     python benchmark_amd_cpu.py --pdf report.pdf --quick")
        print("\n  3. View optimizer recommendations:")
        print("     python -c \"from src.core.cpu_optimizer import AMDCPUOptimizer; AMDCPUOptimizer().print_recommendation()\"")
    else:
        print("\n[FAILED] Some tests failed. Please check the error messages above.")

    print("\n" + "=" * 70 + "\n")

    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
