"""
AMD CPU多核性能优化器

专门针对AMD Ryzen 9 3950X/3990X等16核32线程处理器优化
目标：充分利用所有物理核心，达成最高吞吐量
"""

import psutil
import gc
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemSpec:
    """系统规格"""
    physical_cores: int
    logical_cores: int
    total_memory_gb: float
    available_memory_gb: float


@dataclass
class OptimalConfig:
    """最优配置"""
    max_workers: int
    num_threads: int
    ocr_batch_size: int
    layout_batch_size: int
    table_batch_size: int
    max_process_memory_gb: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'max_workers': self.max_workers,
            'num_threads': self.num_threads,
            'ocr_batch_size': self.ocr_batch_size,
            'layout_batch_size': self.layout_batch_size,
            'table_batch_size': self.table_batch_size,
        }


class AMDCPUOptimizer:
    """
    AMD CPU性能优化器

    智能计算最优配置以充分利用16个物理核心
    """

    # 不同内存配置下的推荐参数
    RECOMMENDED_CONFIGS = {
        # (总内存GB, 是否GPU): {配置}
        (16, False): {'workers': 8, 'batch': 8, 'threads': 16},
        (32, False): {'workers': 16, 'batch': 32, 'threads': 32},
        (64, False): {'workers': 16, 'batch': 48, 'threads': 32},
        (96, False): {'workers': 16, 'batch': 48, 'threads': 32},  # 96GB内存系统
        (32, True): {'workers': 12, 'batch': 48, 'threads': 24},
        (96, True): {'workers': 16, 'batch': 64, 'threads': 32},
    }

    def __init__(self):
        """初始化优化器"""
        self.system = self._detect_system()
        logger.info(f"检测到系统: {self.system.physical_cores}核{self.system.logical_cores}线程, "
                   f"{self.system.total_memory_gb:.1f}GB内存")

    def _detect_system(self) -> SystemSpec:
        """检测系统规格"""
        physical_cores = psutil.cpu_count(logical=False) or 16
        logical_cores = psutil.cpu_count() or 32
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        available_memory_gb = psutil.virtual_memory().available / (1024**3)

        return SystemSpec(
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb
        )

    def calculate_optimal_workers(self) -> int:
        """
        计算最优worker数量

        策略：
        1. CPU密集型：使用物理核心数
        2. 内存密集型：每2GB内存1个worker
        3. 取较小值以确保稳定性
        """
        # 基于CPU
        cpu_based = self.system.physical_cores

        # 基于内存（每2GB内存1个worker）
        mem_based = int(self.system.available_memory_gb / 2)

        # 取较小值，但至少4个
        optimal = min(cpu_based, mem_based)
        return max(optimal, 4)

    def calculate_optimal_batch_size(self, workers: int, use_gpu: bool = False) -> int:
        """
        计算最优批处理大小

        策略：
        - batch_size应该让所有worker保持忙碌
        - 但不能超过内存限制
        - 考虑内存碎片和峰值

        公式：
        batch_size = min(
            内存限制: 可用内存GB × 1.5,
            CPU并行度: workers × 2,
            上限: 根据总内存动态调整
                - 32GB以下: 32
                - 64GB以下: 48
                - 96GB及以上: 64
        )
        """
        if use_gpu:
            # GPU模式：假设有充足显存
            return 64 if self.system.total_memory_gb >= 64 else 48

        # CPU模式
        available_gb = self.system.available_memory_gb
        total_gb = self.system.total_memory_gb

        # 方法1：基于内存（每GB可处理约1.5页）
        mem_based_batch = int(available_gb * 1.5)

        # 方法2：基于CPU并行度（每个worker处理2页）
        cpu_based_batch = workers * 2

        # 方法3：基于核心数（每个物理核心处理2页）
        core_based_batch = self.system.physical_cores * 2

        # 动态上限：根据总内存调整
        if total_gb >= 96:
            upper_limit = 64  # 96GB内存可以使用更大的batch
        elif total_gb >= 64:
            upper_limit = 48
        elif total_gb >= 32:
            upper_limit = 32
        else:
            upper_limit = 16

        # 取三种方法的最小值
        batch_size = min(mem_based_batch, cpu_based_batch, core_based_batch, upper_limit)

        # 设置下限
        batch_size = max(batch_size, 8)

        logger.debug(f"批处理大小计算: 内存={mem_based_batch}, "
                    f"CPU并行={cpu_based_batch}, 核心={core_based_batch}, "
                    f"上限={upper_limit}, 选定={batch_size}")

        return batch_size

    def get_optimal_config(self, enable_gpu: bool = False) -> OptimalConfig:
        """
        获取最优配置

        Returns:
            OptimalConfig: 包含所有优化参数的配置对象
        """
        workers = self.calculate_optimal_workers()
        batch_size = self.calculate_optimal_batch_size(workers, enable_gpu)

        # 表格批处理大小较小（表格处理较重）
        table_batch_size = max(batch_size // 4, 2)

        # 最大进程内存：使用70%可用内存
        max_process_memory_gb = self.system.total_memory_gb * 0.70

        config = OptimalConfig(
            max_workers=workers,
            num_threads=self.system.logical_cores,  # 使用所有逻辑核心
            ocr_batch_size=batch_size,
            layout_batch_size=batch_size,
            table_batch_size=table_batch_size,
            max_process_memory_gb=max_process_memory_gb
        )

        return config

    def print_recommendation(self, enable_gpu: bool = False):
        """打印推荐配置（美化输出）"""
        config = self.get_optimal_config(enable_gpu)

        # 根据内存大小选择配置文件名
        if self.system.total_memory_gb >= 96:
            config_file = "config_amd_cpu_96gb.yaml"
        elif self.system.total_memory_gb >= 64:
            config_file = "config_amd_cpu_64gb.yaml"
        else:
            config_file = "config_amd_cpu_32core.yaml"

        # 根据内存大小估算吞吐量
        if self.system.total_memory_gb >= 96:
            throughput = "0.6-0.8 页/秒"
        elif self.system.total_memory_gb >= 64:
            throughput = "0.5-0.7 页/秒"
        else:
            throughput = "0.4-0.6 页/秒"

        print("\n" + "=" * 70)
        print(" " * 15 + "🚀 AMD CPU 16核心性能优化推荐配置")
        print("=" * 70)

        print(f"\n📊 系统信息:")
        print(f"   物理核心: {self.system.physical_cores} 核")
        print(f"   逻辑核心: {self.system.logical_cores} 线程 (含超线程)")
        print(f"   总内存:   {self.system.total_memory_gb:.1f} GB")
        print(f"   可用内存: {self.system.available_memory_gb:.1f} GB")

        print(f"\n🎯 优化策略:")
        print(f"   运行模式: {'GPU加速' if enable_gpu else '纯CPU模式'}")

        print(f"\n⚙️  推荐配置:")
        print(f"   max_workers:        {config.max_workers:2d}      # 并发worker数")
        print(f"   num_threads:        {config.num_threads:2d}      # 总线程数")
        print(f"   ocr_batch_size:     {config.ocr_batch_size:2d}      # OCR批处理")
        print(f"   layout_batch_size:  {config.layout_batch_size:2d}      # 布局分析批处理")
        print(f"   table_batch_size:   {config.table_batch_size:2d}      # 表格处理批处理")

        print(f"\n💾 预期资源使用:")
        print(f"   CPU利用率:          85-95%")
        print(f"   内存使用:           {config.max_process_memory_gb:.1f} GB (峰值)")
        print(f"   吞吐量:            {throughput}")

        # 生成命令行
        print(f"\n🖥️  推荐命令:")
        cmd = f"pdf2md convert report.pdf "
        cmd += f"--workers {config.max_workers} "
        cmd += f"--batch-size {config.ocr_batch_size}"
        if not enable_gpu:
            cmd += " --no-gpu"
        print(f"   {cmd}")

        # 配置文件方式
        print(f"\n📄 或使用配置文件:")
        print(f"   cp {config_file} config.yaml")
        print(f"   pdf2md convert report.pdf")

        print("\n" + "=" * 70 + "\n")

        return config


class AdvancedMemoryManager:
    """
    高级内存管理器

    支持动态调整和自适应降级
    """

    def __init__(self, max_percent: float = 85.0, max_process_gb: Optional[float] = None):
        """
        初始化内存管理器

        Args:
            max_percent: 最大内存使用百分比
            max_process_gb: 最大进程内存（GB）
        """
        self.max_percent = max_percent
        self.max_process_bytes = int(max_process_gb * 1024**3) if max_process_gb else None

        # 内存使用历史（用于趋势分析）
        self.memory_history = []
        self.max_history = 100

    def get_available_gb(self) -> float:
        """获取可用内存（GB）"""
        return psutil.virtual_memory().available / (1024**3)

    def get_memory_pressure(self) -> str:
        """
        检查内存压力级别

        Returns:
            str: 'low', 'medium', 'high', 'critical'
        """
        available_gb = self.get_available_gb()
        percent = psutil.virtual_memory().percent

        if percent > 90 or available_gb < 2:
            return "critical"
        elif percent > 75 or available_gb < 4:
            return "high"
        elif percent > 60:
            return "medium"
        else:
            return "low"

    def should_reduce_batch_size(self, current_batch_size: int) -> bool:
        """
        是否需要降低批处理大小

        Args:
            current_batch_size: 当前批处理大小

        Returns:
            bool: 是否需要降低
        """
        pressure = self.get_memory_pressure()
        return pressure in ["high", "critical"]

    def recommend_batch_size(self, current_batch_size: int) -> int:
        """
        推荐新的批处理大小

        Args:
            current_batch_size: 当前批处理大小

        Returns:
            int: 推荐的批处理大小
        """
        pressure = self.get_memory_pressure()

        if pressure == "critical":
            # 危急：降低到1/4
            new_size = max(1, current_batch_size // 4)
            logger.warning(f"内存危急({self.get_available_gb():.1f}GB可用)，"
                          f"批处理大小: {current_batch_size} → {new_size}")
            return new_size

        elif pressure == "high":
            # 高压力：降低到1/2
            new_size = max(2, current_batch_size // 2)
            logger.warning(f"内存压力高({self.get_available_gb():.1f}GB可用)，"
                          f"批处理大小: {current_batch_size} → {new_size}")
            return new_size

        else:
            # 正常：保持不变
            return current_batch_size

    def log_stats(self, context: str = ""):
        """记录内存统计"""
        available_gb = self.get_available_gb()
        percent = psutil.virtual_memory().percent
        pressure = self.get_memory_pressure()

        logger.info(f"内存状态[{context}]: "
                   f"可用={available_gb:.1f}GB ({percent}%), "
                   f"压力={pressure}")

        # 记录历史
        self.memory_history.append({
            'context': context,
            'available_gb': available_gb,
            'percent': percent,
            'pressure': pressure
        })

        # 限制历史长度
        if len(self.memory_history) > self.max_history:
            self.memory_history.pop(0)

    def force_cleanup(self):
        """强制清理内存"""
        logger.debug("执行垃圾回收...")
        gc.collect()
        logger.debug(f"清理后可用内存: {self.get_available_gb():.1f}GB")


def print_system_info():
    """打印系统信息"""
    import platform

    print("\n" + "=" * 70)
    print(" " * 20 + "系统信息")
    print("=" * 70)

    # CPU信息
    print(f"\n处理器 (CPU):")
    print(f"   物理核心: {psutil.cpu_count(logical=False)}")
    print(f"   逻辑核心: {psutil.cpu_count()}")
    print(f"   频率: {psutil.cpu_freq().max if psutil.cpu_freq() else 'N/A'} MHz")

    # 内存信息
    mem = psutil.virtual_memory()
    print(f"\n内存 (RAM):")
    print(f"   总容量: {mem.total / (1024**3):.1f} GB")
    print(f"   可用:   {mem.available / (1024**3):.1f} GB")
    print(f"   使用率: {mem.percent}%")

    # 系统信息
    print(f"\n系统:")
    print(f"   平台:   {platform.system()} {platform.release()}")
    print(f"   架构:   {platform.machine()}")

    # Python信息
    print(f"\nPython:")
    print(f"   版本:   {platform.python_version()}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    # 测试代码
    print_system_info()

    optimizer = AMDCPUOptimizer()
    config = optimizer.print_recommendation(enable_gpu=False)

    print("\n推荐配置详情:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
