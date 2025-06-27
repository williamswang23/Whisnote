# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
录音管理模块

提供实时录音、按键监听、音频保存等功能。
"""

import threading
import time
import select
import sys
import signal
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable

import numpy as np
import sounddevice as sd

from ..utils.config import Config
from ..utils.audio_utils import AudioProcessor


class RecordingManager:
    """录音管理器类，负责音频录制和控制"""
    
    def __init__(self) -> None:
        """初始化录音管理器"""
        self.is_recording = False
        self.audio_frames: List[np.ndarray] = []
        self.sample_rate = Config.SAMPLE_RATE
        self.channels = Config.CHANNELS
        self.chunk_size = Config.CHUNK_SIZE
        self.recording_thread: Optional[threading.Thread] = None
        self.input_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def _audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        """
        音频输入回调函数
        
        Args:
            indata: 输入音频数据
            frames: 帧数
            time: 时间信息
            status: 状态信息
        """
        if status:
            print(f"Audio status: {status}")
        
        if self.is_recording:
            # 转换为单声道并保存
            mono_data = AudioProcessor.convert_to_mono(indata.copy())
            self.audio_frames.append(mono_data)
    
    def _monitor_input(self) -> None:
        """监听键盘输入，支持'q'键退出"""
        print("🎙️  Recording started... Press 'q' + Enter or Ctrl+C to stop")
        
        try:
            while self.is_recording and not self.stop_event.is_set():
                # 非阻塞检查是否有输入
                if select.select([sys.stdin], [], [], 0.1) == ([sys.stdin], [], []):
                    user_input = sys.stdin.readline().strip().lower()
                    if user_input == 'q':
                        print("📋 Stopping recording...")
                        self.stop_recording()
                        break
                        
        except KeyboardInterrupt:
            print("\n🛑 Recording interrupted by user")
            self.stop_recording()
    
    def start_recording(self, max_duration: int = Config.DEFAULT_TIMEOUT_SECONDS) -> bool:
        """
        开始录音
        
        Args:
            max_duration: 最大录音时长（秒）
            
        Returns:
            bool: 是否成功开始录音
        """
        if self.is_recording:
            print("🚫 Recording is already in progress")
            return False
        
        try:
            self.is_recording = True
            self.audio_frames.clear()
            self.stop_event.clear()
            
            # 设置信号处理器来处理Ctrl+C
            def signal_handler(signum, frame):
                print("\n🛑 Recording interrupted by signal")
                self.stop_recording()
            
            signal.signal(signal.SIGINT, signal_handler)
            
            # 启动录音流
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=self.chunk_size
            ):
                # 启动输入监听线程
                self.input_thread = threading.Thread(target=self._monitor_input)
                self.input_thread.daemon = True
                self.input_thread.start()
                
                # 等待录音结束或超时
                start_time = time.time()
                last_warning_time = 0
                
                while self.is_recording and not self.stop_event.is_set():
                    elapsed = time.time() - start_time
                    
                    # 在接近超时时给出提醒
                    if elapsed >= max_duration - 60 and elapsed >= last_warning_time + 30:
                        remaining = max_duration - elapsed
                        print(f"⚠️  Recording will auto-stop in {remaining:.0f} seconds. Press 'q' to stop now.")
                        last_warning_time = elapsed
                    
                    if elapsed >= max_duration:
                        print(f"⏰ Maximum recording duration ({max_duration}s) reached")
                        print("💾 Saving current recording to prevent data loss...")
                        self.stop_recording()
                        break
                    time.sleep(0.1)
                
                # 等待输入线程结束
                if self.input_thread and self.input_thread.is_alive():
                    self.input_thread.join(timeout=1.0)
            
            return len(self.audio_frames) > 0
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.is_recording = False
            return False
    
    def stop_recording(self) -> None:
        """停止录音"""
        self.is_recording = False
        self.stop_event.set()
    
    def save_recording(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        保存录音到文件
        
        Args:
            output_path: 输出文件路径，如果为None则自动生成
            
        Returns:
            Optional[Path]: 保存的文件路径，失败返回None
        """
        if not self.audio_frames:
            print("🚫 No audio data to save")
            return None
        
        try:
            # 合并所有音频帧
            audio_data = np.concatenate(self.audio_frames, axis=0)
            
            # 如果没有指定输出路径，自动生成
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # 保存到markdown输出目录的audio子文件夹
                audio_dir = Config.get_output_dir() / "audio"
                audio_dir.mkdir(parents=True, exist_ok=True)
                output_path = audio_dir / f"recorded_{timestamp}.wav"
            
            # 保存音频文件
            success = AudioProcessor.save_audio_array(
                audio_data, output_path, self.sample_rate
            )
            
            if success:
                duration = AudioProcessor.get_audio_duration(output_path)
                print(f"💾 Recording saved: {output_path} ({duration:.1f}s)")
                return output_path
            else:
                print("❌ Failed to save recording")
                return None
                
        except Exception as e:
            print(f"❌ Error saving recording: {e}")
            return None
    
    def get_recording_info(self) -> dict:
        """
        获取当前录音信息
        
        Returns:
            dict: 录音信息字典
        """
        frame_count = len(self.audio_frames)
        duration = frame_count * self.chunk_size / self.sample_rate if frame_count > 0 else 0
        
        return {
            "is_recording": self.is_recording,
            "frame_count": frame_count,
            "duration_seconds": duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels
        } 