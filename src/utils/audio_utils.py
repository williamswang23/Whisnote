# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
音频处理工具模块

提供音频格式转换、验证等工具功能。
"""

import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Tuple, Optional
from .config import Config


class AudioProcessor:
    """音频处理器类"""
    
    @staticmethod
    def validate_audio_file(file_path: Path) -> bool:
        """
        验证音频文件是否有效
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bool: 是否为有效音频文件
        """
        try:
            if not file_path.exists():
                return False
                
            with sf.SoundFile(file_path) as f:
                return f.frames > 0 and f.samplerate > 0
        except Exception:
            return False
    
    @staticmethod
    def get_audio_duration(file_path: Path) -> float:
        """
        获取音频文件时长
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            float: 音频时长（秒）
        """
        try:
            with sf.SoundFile(file_path) as f:
                return f.frames / f.samplerate
        except Exception:
            return 0.0
    
    @staticmethod
    def save_audio_array(
        audio_data: np.ndarray, 
        file_path: Path, 
        sample_rate: int = Config.SAMPLE_RATE
    ) -> bool:
        """
        保存音频数组到文件
        
        Args:
            audio_data: 音频数据数组
            file_path: 输出文件路径
            sample_rate: 采样率
            
        Returns:
            bool: 是否保存成功
        """
        try:
            sf.write(file_path, audio_data, sample_rate)
            return True
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return False
    
    @staticmethod
    def convert_to_mono(audio_data: np.ndarray) -> np.ndarray:
        """
        将多声道音频转换为单声道
        
        Args:
            audio_data: 音频数据数组
            
        Returns:
            np.ndarray: 单声道音频数据
        """
        if len(audio_data.shape) > 1:
            return np.mean(audio_data, axis=1)
        return audio_data
    
    @staticmethod
    def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
        """
        音频归一化处理
        
        Args:
            audio_data: 音频数据数组
            
        Returns:
            np.ndarray: 归一化后的音频数据
        """
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val
        return audio_data 