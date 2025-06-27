# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
配置管理模块

管理应用程序的配置参数和设置。
"""

from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理类"""
    
    # API配置
    DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/inference"
    WHISPER_MODEL = "openai/whisper-large-v3"
    
    # 备选模型（带时间戳，用于更好的标点处理）
    WHISPER_TIMESTAMPED_MODEL = "openai/whisper-timestamped-medium"  # 移除.en支持多语言
    
    # 是否使用带时间戳的模型来改善标点
    USE_TIMESTAMPED_FOR_PUNCTUATION = True
    
    # 音频配置
    SAMPLE_RATE = 44100
    CHANNELS = 1
    DTYPE = "int16"
    CHUNK_SIZE = 1024
    
    # 录音配置
    MIN_RECORDING_SECONDS = 1
    MAX_RECORDING_SECONDS = 1800  # 30分钟，给更大的空间
    DEFAULT_TIMEOUT_SECONDS = 600  # 默认10分钟，更符合您的需求
    
    # 文件配置
    TEMP_DIR = Path("/tmp")
    OUTPUT_DIR = Path.home() / "Desktop" / "voice_transcripts"
    
    # 超时配置
    API_TIMEOUT_SECONDS = 30
    
    # 音频分割配置
    MAX_FILE_SIZE_MB = 25  # DeepInfra文件大小限制
    CHUNK_OVERLAP_SECONDS = 3  # 分割时的重叠时间
    BYTES_PER_SECOND = 88200  # 44100Hz * 1声道 * 2字节 ≈ 86KB/s
    
    @classmethod
    def get_output_dir(cls) -> Path:
        """
        获取输出目录，如果不存在则创建
        
        Returns:
            Path: 输出目录路径
        """
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OUTPUT_DIR
    
    @classmethod
    def get_temp_dir(cls) -> Path:
        """
        获取临时目录
        
        Returns:
            Path: 临时目录路径
        """
        return cls.TEMP_DIR
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        将配置转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "deepinfra_base_url": cls.DEEPINFRA_BASE_URL,
            "whisper_model": cls.WHISPER_MODEL,
            "sample_rate": cls.SAMPLE_RATE,
            "channels": cls.CHANNELS,
            "max_recording_seconds": cls.MAX_RECORDING_SECONDS,
            "output_dir": str(cls.OUTPUT_DIR),
            "temp_dir": str(cls.TEMP_DIR)
        } 