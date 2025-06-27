# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
语音转写服务模块

通过DeepInfra Whisper API将音频文件转换为文本。
"""

import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

from ..utils.config import Config
from ..utils.audio_splitter import AudioSplitter


class TranscriptionService:
    """语音转写服务类"""
    
    def __init__(self, api_token: str) -> None:
        """
        初始化转写服务
        
        Args:
            api_token: DeepInfra API密钥
        """
        self.api_token = api_token
        self.base_url = Config.DEEPINFRA_BASE_URL
        self.model = Config.WHISPER_MODEL
        self.timeout = Config.API_TIMEOUT_SECONDS
        self.splitter = AudioSplitter()
        
    def transcribe_file(
        self, 
        audio_file: Path, 
        language: str = "zh"
    ) -> Optional[str]:
        """
        转写音频文件
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码，默认为auto自动检测（DeepInfra会自动检测）
            
        Returns:
            Optional[str]: 转写文本，失败返回None
        """
        if not audio_file.exists():
            print(f"❌ Audio file not found: {audio_file}")
            return None
            
        url = f"{self.base_url}/{self.model}"
        
        headers = {
            "Authorization": f"bearer {self.api_token}"
        }
        
        # 准备文件和参数 - DeepInfra使用不同的格式
        try:
            with open(audio_file, "rb") as f:
                files = {
                    "audio": (audio_file.name, f, "audio/wav")
                }
                
                # 准备API参数
                data = {}
                if language and language != "auto":
                    data["language"] = language
                
                print(f"🔄 Uploading audio to DeepInfra... ({audio_file.name})")
                if language != "auto":
                    print(f"🌐 Language specified: {language}")
                
                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                # 解析DeepInfra响应格式
                result = response.json()
                
                # 保留原始响应用于调试（仅控制台输出）
                print(f"🔍 API Response: {result}")
                
                # 获取转写文本，保留原始格式（包括空格分隔）
                transcript = result.get("text", "")
                
                # 检查原始文本是否有标点符号或空格分隔
                if self._has_adequate_punctuation(transcript):
                    print("✅ Original text has adequate punctuation, using as-is")
                elif self._has_word_spacing(transcript):
                    print("📝 Original text has word spacing, using as-is")
                else:
                    print("⚠️  Original text lacks both punctuation and spacing, attempting improvement...")
                    # 尝试使用时间戳模型改善
                    if Config.USE_TIMESTAMPED_FOR_PUNCTUATION and language in ["zh", "auto"]:
                        improved_transcript = self._transcribe_with_timestamps(audio_file, language)
                        if improved_transcript and len(improved_transcript) > len(transcript):
                            print("✅ Improved transcript using timestamped model")
                            transcript = improved_transcript
                        else:
                            print("📝 Timestamped model didn't improve, using original")
                
                if transcript:
                    print(f"✅ Transcription completed ({len(transcript)} characters)")
                    return transcript
                else:
                    print("⚠️  Empty transcription result")
                    return None
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ API request error: {e}")
            return None
        except FileNotFoundError:
            print(f"❌ Could not read audio file: {audio_file}")
            return None
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def check_api_status(self) -> bool:
        """
        检查API连接状态
        
        Returns:
            bool: API是否可用
        """
        # 简化的状态检查：如果有token就认为可用
        # 实际的API测试会在转写时进行
        return len(self.api_token) > 10
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表
        
        Returns:
            Dict[str, str]: 语言代码和名称的映射
        """
        # Whisper支持的主要语言
        return {
            "auto": "Auto Detect",
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ru": "Russian",
            "ar": "Arabic",
            "hi": "Hindi",
            "pt": "Portuguese",
            "it": "Italian"
        }
    
    def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        估算转写成本（基于DeepInfra的定价）
        
        Args:
            audio_duration_seconds: 音频时长（秒）
            
        Returns:
            float: 估算成本（美元）
        """
        # DeepInfra Whisper定价大约是$0.006/分钟
        # 这个数字可能会变化，仅供参考
        cost_per_minute = 0.006
        minutes = audio_duration_seconds / 60.0
        return minutes * cost_per_minute
    
    def get_transcription_info(self) -> Dict[str, Any]:
        """
        获取转写服务信息
        
        Returns:
            Dict[str, Any]: 服务信息
        """
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "has_token": bool(self.api_token),
            "token_prefix": self.api_token[:10] + "..." if self.api_token else None
        }
    
    def transcribe_large_file(self, audio_file: Path, language: str = "zh") -> Optional[str]:
        """
        转写大音频文件，支持自动分割和拼合
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码，默认为auto自动检测
            
        Returns:
            Optional[str]: 转写文本，失败返回None
        """
        if not audio_file.exists():
            print(f"❌ Audio file not found: {audio_file}")
            return None
        
        # 检查文件大小是否需要分割
        if not self.splitter.need_split(audio_file):
            print("📝 File size is acceptable, processing directly...")
            return self.transcribe_file(audio_file, language)
        
        # 文件需要分割
        file_size_mb = audio_file.stat().st_size / (1024 * 1024)
        print(f"📏 Large file detected ({file_size_mb:.1f}MB), splitting for processing...")
        
        # 创建临时目录用于分片
        temp_dir = Config.get_temp_dir() / f"chunks_{audio_file.stem}"
        
        try:
            # 分割音频文件
            chunk_files = self.splitter.split_audio_file(audio_file, temp_dir)
            
            if len(chunk_files) == 1:
                # 分割失败，直接处理原文件
                return self.transcribe_file(audio_file, language)
            
            # 按顺序转写所有分片
            print(f"🔄 Transcribing {len(chunk_files)} chunks in order...")
            transcripts = []
            
            for i, chunk_file in enumerate(chunk_files):
                print(f"📝 Processing chunk {i+1}/{len(chunk_files)}: {chunk_file.name}")
                
                chunk_transcript = self.transcribe_file(chunk_file, language)
                if chunk_transcript:
                    transcripts.append({
                        "index": i,
                        "text": chunk_transcript.strip(),
                        "file": chunk_file.name
                    })
                    # 添加小延迟避免API限制
                    time.sleep(1)
                else:
                    print(f"⚠️  Warning: Failed to transcribe chunk {i+1}")
            
            # 拼合转写结果
            if transcripts:
                combined_text = self._combine_transcripts(transcripts)
                print(f"✅ Combined transcription completed ({len(combined_text)} characters)")
                return combined_text
            else:
                print("❌ No successful transcriptions from chunks")
                return None
                
        except Exception as e:
            print(f"❌ Error processing large file: {e}")
            return None
        finally:
            # 清理临时分片文件
            if 'chunk_files' in locals():
                self.splitter.cleanup_chunks(chunk_files)
            # 清理临时目录
            try:
                if temp_dir.exists():
                    temp_dir.rmdir()
            except Exception:
                pass
    
    def _combine_transcripts(self, transcripts: List[Dict[str, Any]]) -> str:
        """
        智能拼合转写文本，处理重叠部分
        
        Args:
            transcripts: 转写结果列表
            
        Returns:
            str: 拼合后的完整文本
        """
        if not transcripts:
            return ""
        
        if len(transcripts) == 1:
            return transcripts[0]["text"]
        
        # 按索引排序确保顺序正确
        transcripts.sort(key=lambda x: x["index"])
        
        combined_parts = []
        
        for i, transcript in enumerate(transcripts):
            text = transcript["text"]
            
            if i == 0:
                # 第一段直接添加
                combined_parts.append(text)
            else:
                # 后续段落需要处理重叠
                prev_text = combined_parts[-1]
                current_text = text
                
                # 简单的重叠处理：查找可能的重复词汇
                merged_text = self._merge_overlapping_text(prev_text, current_text)
                
                # 如果没有找到明显重叠，直接连接
                if merged_text:
                    combined_parts[-1] = merged_text
                else:
                    combined_parts.append(current_text)
        
        # 保留原始空格分隔，连接所有部分
        if len(combined_parts) == 1:
            result = combined_parts[0]
        else:
            # 用单个空格连接各部分，保持原有的空格分隔
            result = " ".join(combined_parts)
        
        # 轻度清理：只去除首尾空格，保留内部空格分隔
        result = result.strip()
        
        return result
    
    def _merge_overlapping_text(self, prev_text: str, current_text: str) -> Optional[str]:
        """
        合并有重叠的文本段落
        
        Args:
            prev_text: 前一段文本
            current_text: 当前段文本
            
        Returns:
            Optional[str]: 合并后的文本，如果没有找到重叠则返回None
        """
        # 获取前一段的最后几个词和当前段的前几个词
        prev_words = prev_text.split()
        current_words = current_text.split()
        
        # 检查最多10个词的重叠
        max_overlap = min(10, len(prev_words), len(current_words))
        
        for overlap_len in range(max_overlap, 0, -1):
            prev_end = prev_words[-overlap_len:]
            current_start = current_words[:overlap_len]
            
            # 检查是否有相似的词汇序列
            if self._words_similar(prev_end, current_start):
                # 找到重叠，合并文本
                merged_words = prev_words + current_words[overlap_len:]
                return " ".join(merged_words)
        
        return None
    
    def _words_similar(self, words1: List[str], words2: List[str]) -> bool:
        """
        检查两个词汇序列是否相似
        
        Args:
            words1: 第一个词汇序列
            words2: 第二个词汇序列
            
        Returns:
            bool: 是否相似
        """
        if len(words1) != len(words2):
            return False
        
        # 计算相似度
        similar_count = 0
        for w1, w2 in zip(words1, words2):
            if w1.lower() == w2.lower():
                similar_count += 1
        
        # 如果80%以上的词汇相同，认为是重叠
        similarity = similar_count / len(words1)
        return similarity >= 0.8
    
    def _needs_punctuation_improvement(self, text: str) -> bool:
        """
        判断文本是否需要标点符号改善
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否需要改善
        """
        if not text or len(text) < 10:  # 降低最小长度要求
            return False
        
        # 计算标点符号密度
        punctuation_chars = set('。，！？；：""''（）【】《》、')
        punctuation_count = sum(1 for char in text if char in punctuation_chars)
        
        # 如果标点符号少于文本长度的1%，认为需要改善
        punctuation_density = punctuation_count / len(text)
        
        print(f"📊 Punctuation analysis: {punctuation_count} punctuation marks in {len(text)} characters (density: {punctuation_density:.3f})")
        
        return punctuation_density < 0.01  # 降低阈值
    
    def _transcribe_with_timestamps(self, audio_file: Path, language: str) -> Optional[str]:
        """
        使用带时间戳的模型进行转写，提取语义分段信息
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码
            
        Returns:
            Optional[str]: 改善后的转写文本
        """
        try:
            url = f"{self.base_url}/{Config.WHISPER_TIMESTAMPED_MODEL}"
            
            headers = {
                "Authorization": f"bearer {self.api_token}"
            }
            
            with open(audio_file, "rb") as f:
                files = {
                    "audio": (audio_file.name, f, "audio/wav")
                }
                
                data = {}
                if language and language != "auto":
                    data["language"] = language
                
                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 从时间戳信息中提取并改善文本
                return self._process_timestamped_response(result)
                
        except Exception as e:
            print(f"⚠️  Timestamped model failed: {e}")
            return None
    
    def _process_timestamped_response(self, result: Dict[str, Any]) -> Optional[str]:
        """
        处理带时间戳的响应，优先保留原始标点，必要时根据时间间隔添加
        
        Args:
            result: API响应结果
            
        Returns:
            Optional[str]: 处理后的文本
        """
        try:
            # 首先检查是否有原始文本带标点
            original_text = result.get("text", "")
            if self._has_adequate_punctuation(original_text):
                print("📝 Original text has adequate punctuation, using as-is")
                return original_text
            
            # 如果原始文本没有足够标点，使用segments进行处理
            segments = result.get("segments", [])
            if not segments:
                return original_text
            
            print(f"📝 Processing {len(segments)} segments to add punctuation...")
            processed_text = ""
            
            for i, segment in enumerate(segments):
                text = segment.get("text", "").strip()
                if not text:
                    continue
                
                # 添加空格分隔（如果不是第一个segment）
                if i > 0 and processed_text and not processed_text.endswith(" "):
                    processed_text += " "
                
                # 检查当前段落是否已有标点
                if self._ends_with_punctuation(text):
                    processed_text += text
                else:
                    # 根据时间间隔决定标点（调整适应快语速）
                    if i < len(segments) - 1:
                        current_end = segment.get("end", 0)
                        next_start = segments[i + 1].get("start", 0)
                        gap = next_start - current_end
                        
                        # 调整时间间隔适应快语速
                        if gap > 1.5:  # 长停顿，句子结束（从2.0降至1.5）
                            text += "。"
                        elif gap > 0.8:  # 中等停顿，逗号（从1.0降至0.8）
                            text += "，"
                        elif gap > 0.3:  # 短停顿，顿号（从0.5降至0.3）
                            text += "、"
                        # 没有明显停顿，在segment间添加空格分隔
                    else:
                        # 最后一个段落，添加句号
                        text += "。"
                
                processed_text += text
            
            return processed_text if processed_text else original_text
            
        except Exception as e:
            print(f"⚠️  Error processing timestamped response: {e}")
            return result.get("text", "")
    
    def _has_adequate_punctuation(self, text: str) -> bool:
        """
        检查文本是否有足够的标点符号
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否有足够标点
        """
        if not text or len(text) < 20:
            return False
        
        # 计算标点符号密度
        punctuation_chars = set('。，！？；：""''（）【】《》、')
        punctuation_count = sum(1 for char in text if char in punctuation_chars)
        
        # 如果标点符号大于文本长度的2%，认为足够（降低阈值）
        punctuation_density = punctuation_count / len(text)
        return punctuation_density >= 0.02
    
    def _has_word_spacing(self, text: str) -> bool:
        """
        检查文本是否有合理的词汇空格分隔
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否有词汇分隔
        """
        if not text or len(text) < 10:
            return False
        
        # 计算空格密度
        space_count = text.count(' ')
        
        # 如果有空格且空格数量合理（不是只有1个空格的长文本）
        if space_count == 0:
            return False
        
        # 对于较短文本，有空格就算合理
        if len(text) < 30:
            return space_count > 0
        
        # 对于较长文本，要求合理的空格密度（至少每20个字符有1个空格）
        space_density = space_count / len(text)
        return space_density >= 0.05  # 大约每20个字符1个空格
    
    def _ends_with_punctuation(self, text: str) -> bool:
        """
        检查文本是否以标点符号结尾
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否以标点结尾
        """
        if not text:
            return False
        
        punctuation_chars = set('。，！？；：、')
        return text[-1] in punctuation_chars
    
 