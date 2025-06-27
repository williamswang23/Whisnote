# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
音频分割工具模块

提供大音频文件分割功能，确保每个分片不超过API限制。
"""

import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Tuple
from .config import Config


class AudioSplitter:
    """音频分割器类"""
    
    def __init__(self) -> None:
        """初始化音频分割器"""
        self.max_size_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
        self.overlap_seconds = Config.CHUNK_OVERLAP_SECONDS
    
    def need_split(self, file_path: Path) -> bool:
        """
        检查文件是否需要分割
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bool: 是否需要分割
        """
        try:
            file_size = file_path.stat().st_size
            return file_size > self.max_size_bytes
        except Exception:
            return False
    
    def calculate_chunk_duration(self, file_path: Path) -> float:
        """
        计算每个分片的最佳时长
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            float: 每个分片的时长（秒）
        """
        try:
            with sf.SoundFile(file_path) as f:
                total_duration = f.frames / f.samplerate
                file_size = file_path.stat().st_size
                
                # 计算每秒的字节数
                bytes_per_second = file_size / total_duration
                
                # 计算每个分片的最大时长（留一些余量）
                max_chunk_duration = (self.max_size_bytes * 0.9) / bytes_per_second
                
                # 确保不少于60秒，不超过300秒（5分钟）
                return max(60.0, min(300.0, max_chunk_duration))
                
        except Exception:
            return 240.0  # 默认4分钟
    
    def split_audio_file(self, file_path: Path, output_dir: Path) -> List[Path]:
        """
        分割音频文件为多个小文件
        
        Args:
            file_path: 原始音频文件路径
            output_dir: 输出目录
            
        Returns:
            List[Path]: 分割后的文件列表（按顺序）
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 读取音频文件
            audio_data, sample_rate = sf.read(file_path)
            total_duration = len(audio_data) / sample_rate
            
            # 计算分片参数
            chunk_duration = self.calculate_chunk_duration(file_path)
            overlap_samples = int(self.overlap_seconds * sample_rate)
            chunk_samples = int(chunk_duration * sample_rate)
            
            print(f"🔧 Splitting large audio file ({total_duration:.1f}s) into chunks of {chunk_duration:.1f}s")
            
            chunk_files = []
            chunk_start = 0
            chunk_index = 0
            
            while chunk_start < len(audio_data):
                # 计算当前分片的结束位置
                chunk_end = min(chunk_start + chunk_samples, len(audio_data))
                
                # 提取音频分片
                chunk_audio = audio_data[chunk_start:chunk_end]
                
                # 生成分片文件名
                base_name = file_path.stem
                chunk_filename = f"{base_name}_chunk_{chunk_index:03d}.wav"
                chunk_path = output_dir / chunk_filename
                
                # 保存分片
                sf.write(chunk_path, chunk_audio, sample_rate)
                chunk_files.append(chunk_path)
                
                chunk_duration_actual = len(chunk_audio) / sample_rate
                print(f"  📄 Created chunk {chunk_index}: {chunk_filename} ({chunk_duration_actual:.1f}s)")
                
                # 计算下一个分片的起始位置（考虑重叠）
                if chunk_end >= len(audio_data):
                    break
                
                chunk_start = chunk_end - overlap_samples
                chunk_index += 1
            
            print(f"✅ Audio split into {len(chunk_files)} chunks")
            return chunk_files
            
        except Exception as e:
            print(f"❌ Error splitting audio file: {e}")
            return [file_path]  # 如果分割失败，返回原文件
    
    def cleanup_chunks(self, chunk_files: List[Path]) -> None:
        """
        清理临时分片文件
        
        Args:
            chunk_files: 要清理的文件列表
        """
        for chunk_file in chunk_files:
            try:
                if chunk_file.exists():
                    chunk_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to cleanup {chunk_file}: {e}")
    
    def get_chunk_info(self, chunk_files: List[Path]) -> List[dict]:
        """
        获取分片信息
        
        Args:
            chunk_files: 分片文件列表
            
        Returns:
            List[dict]: 分片信息列表
        """
        chunk_info = []
        
        for i, chunk_file in enumerate(chunk_files):
            try:
                with sf.SoundFile(chunk_file) as f:
                    duration = f.frames / f.samplerate
                    size_mb = chunk_file.stat().st_size / (1024 * 1024)
                    
                    chunk_info.append({
                        "index": i,
                        "file": chunk_file,
                        "duration": duration,
                        "size_mb": size_mb
                    })
            except Exception:
                chunk_info.append({
                    "index": i,
                    "file": chunk_file,
                    "duration": 0,
                    "size_mb": 0
                })
        
        return chunk_info 