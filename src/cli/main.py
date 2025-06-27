# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
CLI主入口模块

整合录音、转写、输出等功能，提供完整的命令行界面。
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.recorder import RecordingManager
from ..core.transcriber import TranscriptionService
from ..core.markdown_writer import MarkdownWriter
from ..core.security import SecurityManager
from ..utils.config import Config
from ..utils.audio_utils import AudioProcessor

# 创建Typer应用和Rich控制台
app = typer.Typer(help="🎙️ Voice Recording and Transcription Tool")
console = Console()


class VoiceTranscriptionApp:
    """语音转写应用主类"""
    
    def __init__(self) -> None:
        """初始化应用"""
        self.security_manager = SecurityManager()
        self.recorder = RecordingManager()
        self.markdown_writer = MarkdownWriter()
        self.transcription_service: Optional[TranscriptionService] = None
        
    def initialize_transcription_service(self) -> bool:
        """
        初始化转写服务
        
        Returns:
            bool: 是否成功初始化
        """
        try:
            token = self.security_manager.get_deepinfra_token()
            if not self.security_manager.validate_api_key(token):
                console.print("❌ Invalid API key format", style="red")
                return False
                
            self.transcription_service = TranscriptionService(token)
            return True
            
        except RuntimeError as e:
            console.print(f"❌ {e}", style="red")
            return False
    
    def record_and_transcribe(
        self, 
        max_duration: int = Config.DEFAULT_TIMEOUT_SECONDS,
        language: str = "zh",
        save_daily_log: bool = True
    ) -> bool:
        """
        执行录音和转写流程
        
        Args:
            max_duration: 最大录音时长（秒）
            language: 转写语言
            save_daily_log: 是否保存到日志
            
        Returns:
            bool: 是否成功完成
        """
        audio_file_path = None
        
        try:
            # 1. 录音
            console.print("🎙️ Starting recording...", style="green")
            
            if not self.recorder.start_recording(max_duration):
                console.print("❌ Failed to start recording", style="red")
                return False
            
            # 2. 保存录音
            audio_file_path = self.recorder.save_recording()
            if not audio_file_path:
                console.print("❌ Failed to save recording", style="red")
                return False
            
            # 3. 询问用户是否上传转写
            should_transcribe = typer.confirm(
                "\n📤 Upload and transcribe this recording?",
                default=True
            )
            
            if not should_transcribe:
                console.print("🗑️ Recording discarded", style="yellow")
                self.security_manager.secure_delete_file(audio_file_path)
                return False
            
            # 4. 转写音频
            console.print("🔄 Transcribing audio...", style="blue")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Uploading to DeepInfra...", total=None)
                
                transcript = self.transcription_service.transcribe_file(
                    audio_file_path, language
                )
                
                progress.update(task, description="Transcription complete!")
            
            if not transcript:
                console.print("❌ Transcription failed", style="red")
                return False
            
            # 5. 显示转写预览
            preview_length = 120
            preview = transcript[:preview_length] + ("..." if len(transcript) > preview_length else "")
            console.print(f"\n📝 Transcript preview:\n{preview}\n", style="cyan")
            
            # 6. 保存Markdown
            audio_duration = AudioProcessor.get_audio_duration(audio_file_path)
            metadata = {
                "duration_seconds": round(audio_duration, 2),
                "file_size_mb": round(audio_file_path.stat().st_size / (1024 * 1024), 2),
                "language": language,
                "word_count": len(transcript.split()),
                "character_count": len(transcript)
            }
            
            # 保存独立文件
            markdown_path = self.markdown_writer.save_transcription(
                transcript, audio_file_path, metadata
            )
            
            # 保存到日志（可选）
            if save_daily_log:
                self.markdown_writer.append_to_daily_log(transcript, audio_file_path)
            
            # 音频文件已保存到audio/文件夹，不删除
            
            console.print("✅ Transcription completed successfully!", style="green")
            return True
            
        except KeyboardInterrupt:
            console.print("\n🛑 Process interrupted by user", style="yellow")
            # 音频文件保留，用户可能需要手动处理
            return False
        except Exception as e:
            console.print(f"❌ Unexpected error: {e}", style="red")
            # 音频文件保留，便于调试
            return False
    
    def transcribe_existing_file(self, file_path: Path, language: str = "zh") -> bool:
        """
        转写现有音频文件（支持大文件自动分割）
        
        Args:
            file_path: 音频文件路径
            language: 转写语言
            
        Returns:
            bool: 是否成功
        """
        try:
            if not AudioProcessor.validate_audio_file(file_path):
                console.print(f"❌ Invalid or missing audio file: {file_path}", style="red")
                return False
            
            # 检查文件大小并选择适当的转写方法
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            console.print(f"🔄 Transcribing file: {file_path.name} ({file_size_mb:.1f}MB)", style="blue")
            
            # 使用大文件转写方法（自动处理分割）
            transcript = self.transcription_service.transcribe_large_file(file_path, language)
            if not transcript:
                console.print("❌ Transcription failed", style="red")
                return False
            
            # 显示预览
            preview = transcript[:120] + ("..." if len(transcript) > 120 else "")
            console.print(f"\n📝 Transcript:\n{preview}\n", style="cyan")
            
            # 保存结果
            duration = AudioProcessor.get_audio_duration(file_path)
            metadata = {
                "duration_seconds": round(duration, 2),
                "file_size_mb": round(file_size_mb, 2),
                "language": language,
                "source_file": str(file_path),
                "word_count": len(transcript.split()),
                "character_count": len(transcript),
                "processing_method": "chunked" if file_size_mb > 25 else "direct"
            }
            
            self.markdown_writer.save_transcription(transcript, file_path, metadata)
            
            console.print("✅ File transcription completed!", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Error transcribing file: {e}", style="red")
            return False


# 全局应用实例
voice_app = VoiceTranscriptionApp()


# 录音功能的通用实现
def _record_command(
    max_duration: int = typer.Option(
        Config.DEFAULT_TIMEOUT_SECONDS,
        "--max-duration", "-d",
        help=f"Maximum recording duration in seconds (default: {Config.DEFAULT_TIMEOUT_SECONDS}s = {Config.DEFAULT_TIMEOUT_SECONDS//60}min, max: {Config.MAX_RECORDING_SECONDS}s = {Config.MAX_RECORDING_SECONDS//60}min)"
    ),
    language: str = typer.Option(
        "zh",
        "--language", "-l",
        help="Language for transcription (zh, en, auto, etc.)"
    ),
    no_daily_log: bool = typer.Option(
        False,
        "--no-daily-log",
        help="Skip adding to daily log file"
    )
):
    """录音功能的通用实现"""
    # 初始化转写服务
    if not voice_app.initialize_transcription_service():
        raise typer.Exit(1)
    
    # 执行录音和转写
    success = voice_app.record_and_transcribe(
        max_duration=max_duration,
        language=language,
        save_daily_log=not no_daily_log
    )
    
    if not success:
        raise typer.Exit(1)


@app.command()
def record(
    max_duration: int = typer.Option(
        Config.DEFAULT_TIMEOUT_SECONDS,
        "--max-duration", "-d",
        help=f"Maximum recording duration in seconds (default: {Config.DEFAULT_TIMEOUT_SECONDS}s = {Config.DEFAULT_TIMEOUT_SECONDS//60}min, max: {Config.MAX_RECORDING_SECONDS}s = {Config.MAX_RECORDING_SECONDS//60}min)"
    ),
    language: str = typer.Option(
        "zh",
        "--language", "-l",
        help="Language for transcription (zh, en, auto, etc.)"
    ),
    no_daily_log: bool = typer.Option(
        False,
        "--no-daily-log",
        help="Skip adding to daily log file"
    )
):
    """🎙️ Start recording and transcribe to Markdown"""
    _record_command(max_duration, language, no_daily_log)


@app.command(name="r")
def record_short(
    max_duration: int = typer.Option(
        Config.DEFAULT_TIMEOUT_SECONDS,
        "--max-duration", "-d",
        help=f"Maximum recording duration in seconds (default: {Config.DEFAULT_TIMEOUT_SECONDS}s = {Config.DEFAULT_TIMEOUT_SECONDS//60}min, max: {Config.MAX_RECORDING_SECONDS}s = {Config.MAX_RECORDING_SECONDS//60}min)"
    ),
    language: str = typer.Option(
        "zh",
        "--language", "-l",
        help="Language for transcription (zh, en, auto, etc.)"
    ),
    no_daily_log: bool = typer.Option(
        False,
        "--no-daily-log",
        help="Skip adding to daily log file"
    )
):
    """🎙️ Start recording and transcribe to Markdown (shortcut for 'record')"""
    _record_command(max_duration, language, no_daily_log)


# 转写功能的通用实现
def _transcribe_command(
    file_path: Path = typer.Argument(..., help="Audio file to transcribe"),
    language: str = typer.Option(
        "zh",
        "--language", "-l",
        help="Language for transcription"
    )
):
    """转写功能的通用实现"""
    # 初始化转写服务
    if not voice_app.initialize_transcription_service():
        raise typer.Exit(1)
    
    # 转写文件
    success = voice_app.transcribe_existing_file(file_path, language)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def transcribe(
    file_path: Path = typer.Argument(..., help="Audio file to transcribe"),
    language: str = typer.Option(
        "zh",
        "--language", "-l",
        help="Language for transcription"
    )
):
    """📄 Transcribe an existing audio file"""
    _transcribe_command(file_path, language)


@app.command(name="t")
def transcribe_short(
    file_path: Path = typer.Argument(..., help="Audio file to transcribe"),
    language: str = typer.Option(
        "zh",
        "--language", "-l",
        help="Language for transcription"
    )
):
    """📄 Transcribe an existing audio file (shortcut for 'transcribe')"""
    _transcribe_command(file_path, language)


@app.command()
def status():
    """📊 Show system status and statistics"""
    
    try:
        # API状态
        if voice_app.initialize_transcription_service():
            api_status = voice_app.transcription_service.check_api_status()
            console.print(f"🔗 API Status: {'✅ Connected' if api_status else '❌ Failed'}")
        else:
            console.print("🔗 API Status: ❌ Not configured")
        
        # 录音设备状态
        import sounddevice as sd
        devices = sd.query_devices()
        default_input = sd.default.device[0] if sd.default.device else None
        console.print(f"🎤 Audio Input: {devices[default_input]['name'] if default_input is not None else 'None'}")
        
        # 文件统计
        stats = voice_app.markdown_writer.get_stats()
        console.print(f"📁 Output Directory: {stats['output_dir']}")
        console.print(f"📄 Total Files: {stats['total_files']}")
        console.print(f"💾 Total Size: {stats['total_size_mb']} MB")
        
        if stats['recent_files']:
            console.print("\n📋 Recent Files:")
            for file_name in stats['recent_files']:
                console.print(f"  • {file_name}")
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def config():
    """⚙️ Show configuration information"""
    
    config_info = Config.to_dict()
    
    console.print("⚙️ Configuration:")
    for key, value in config_info.items():
        console.print(f"  • {key}: {value}")


def main():
    """主入口函数，处理默认命令"""
    import sys
    
    # 如果没有提供参数，默认执行 record 命令
    if len(sys.argv) == 1:
        sys.argv.append("record")
    
    app()


if __name__ == "__main__":
    main()