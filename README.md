# 🎙️ Whisnote：您的智能语音转写助手


[![Python 版本](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![平台](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#-系统要求)

**一款强大、优先本地的 macOS 命令行工具，能将您的语音笔记和音频文件转换成格式精美、内容智能的 Markdown 文档。**

<!-- TODO: 在此添加 GIF 动画演示 -->
<!-- <p align="center">
  <img src="path/to/your/demo.gif" alt="Whisnote 演示" width="800"/>
</p> -->

无论您是录制会议、捕捉灵感，还是转写讲座，Whisnote 都能简化整个流程。它利用 DeepInfra API 实现高精度转写，并处理从录音到安全密钥管理、再到智能格式化输出的所有后续工作。

## 🌟 核心功能

- **🎤 一键录音:** 只需输入 `voice` 即可开始录音。按 `q` 停止，您的音频便即刻准备好转写。
- **📁 大文件支持:** 自动将超过 25MB 的大音频文件分割成易于管理的小块进行可靠转写，然后智能地将文本重新拼接。
- **✍️ 智能标点:** 采用多层策略来恢复标点和格式，确保您的转写文本可读性强、结构清晰。
- **🔐 安全的钥匙串存储:** 您的 DeepInfra API 密钥被安全地存储在 macOS 钥匙串中，而不是在纯文本文件中。
- **📄 精美的 Markdown 输出:** 转写稿被保存为干净的 Markdown 文件，并附有字数、时长和原始音频文件链接等元数据。
- **📔 每日日志:** 自动将笔记整理到 `daily_log_YYYYMMDD.md` 文件中，便于回顾。

## 💻 系统要求

- **操作系统:** macOS (用于钥匙串集成)
- **Python:** 3.8 或更高版本
- **硬件:** 一个可用的麦克风用于录音

## 🚀 安装与设置

只需三步，即可轻松上手。

### 1. 克隆仓库

```bash
# 当您有了仓库 URL 后，替换此处的链接
git clone https://github.com/williamswang23/Whisnote.git
cd Whisnote
```

### 2. 安装依赖

推荐使用虚拟环境。

```bash
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 以可编辑模式安装工具
pip install -e .
```

### 3. 配置 API 密钥 (macOS 钥匙串)

本工具需要 [DeepInfra](https://deepinfra.com/) 提供的 API 密钥。获取密钥后，使用一个简单的命令将其安全地存储在您的 macOS 钥匙串中。

工具将在钥匙串中查找服务名称为 `deepinfra` 的条目。

```bash
# 将 "YOUR_API_KEY_HERE" 替换为您的真实 DeepInfra 令牌
security add-generic-password \
  -a "$USER" \
  -s "deepinfra" \
  -w "YOUR_API_KEY_HERE" \
  -T "$(which python)"
```

要验证密钥是否已存储成功，可以运行 `voice config`。如果成功，它将显示一个经过脱敏处理的密钥。

## 🔗 设置终端别名 (推荐)

为了在任何目录下都能直接使用 `voice` 命令，建议设置一个终端别名。

### 自动设置别名

在项目目录下运行以下命令，将自动为您添加别名到shell配置文件：

```bash
# 对于 zsh 用户 (macOS 默认)
echo "alias voice='python $(pwd)/voice_cli.py'" >> ~/.zshrc
source ~/.zshrc

# 对于 bash 用户
echo "alias voice='python $(pwd)/voice_cli.py'" >> ~/.bashrc
source ~/.bashrc
```

### 手动设置别名

您也可以手动编辑shell配置文件：

```bash
# 编辑 zsh 配置文件
nano ~/.zshrc

# 在文件末尾添加以下行 (将路径替换为您的实际项目路径)
alias voice='python /path/to/your/Whisnote/voice_cli.py'

# 保存文件后重新加载配置
source ~/.zshrc
```

### 验证别名设置

设置完成后，您可以在任何目录下测试：

```bash
# 测试别名是否生效
voice --help

# 查看当前设置的别名
alias | grep voice
```

如果看到帮助信息，说明别名设置成功！现在您可以在系统的任何位置使用 `voice` 命令了。

## 🎤 使用方法

Whisnote 的设计直观易用。

### 实时录音与转写

默认命令会启动一个录音会话。

```bash
# 使用默认设置开始录音 (最长10分钟，中文)
voice

# 或者更明确地使用
voice record
```
- 按 `q` 后加 `回车` 可随时停止录音。
- 如果达到最大时长，录音将自动停止。
- 停止后，系统会提示您确认是否上传以进行转写。

### 转写现有音频文件

您也可以转写已有的音频文件。支持的格式包括 `.wav`、`.mp3`、`.m4a` 和 `.flac`。

```bash
# 转写一个文件
voice transcribe path/to/your/audio.wav

# 使用简写命令
voice t path/to/your/audio.m4a
```

### 命令行选项

使用这些选项自定义工具的行为：

| 命令         | 选项             | 简写 | 描述                                       | 默认值 |
|--------------|------------------|------|--------------------------------------------|--------|
| `record`     | `--max-duration` | `-d` | 最大录音时长 (秒)。                        | `600`  |
| `record`     | `--language`     | `-l` | 转写语言 (例如 `en`, `zh`)。               | `zh`   |
| `record`     | `--no-daily-log` |      | 不将转写稿附加到每日日志。                 | `False`|
| `transcribe` | `file_path`      |      | 要转写的音频文件路径。                     |        |
| `transcribe` | `--language`     | `-l` | 转写语言。                                 | `zh`   |

## 🛠️ 工作原理

<details>
<summary><strong>点击查看技术细节</strong></summary>

### 大文件处理
当音频文件超过 25MB 时，工具会自动执行以下步骤：
1.  **计算最佳分片:** 确定最佳的片段时长，以确保每个分片都小于 API 的大小限制。
2.  **带重叠分割:** 将音频切分成带有 3 秒重叠的片段，以确保在拼接处不会丢失任何词语。
3.  **顺序转写:** 逐个发送每个分片进行转写。
4.  **智能合并:** 通过识别并移除重叠部分的文本来重建完整的转写稿，从而生成一份无缝的最终文档。

### 智能标点
转写 API 有时返回的文本可能没有标点，特别是对于某些语言。本工具使用三层策略来解决这个问题：
1.  **检查标点:** 如果 API 返回的转写稿带有标点，则直接使用。
2.  **检查空格:** 如果没有标点但单词之间有适当的空格，则保留原样。
3.  **基于时间戳的增强:** 作为最后手段，音频将被发送到一个备用的、能感知时间戳的模型 (`whisper-timestamped`)，该模型更擅长推断句子结构。然后使用改进后的文本。

### 文件组织
所有输出文件都会被整齐地组织在您桌面上的 `voice_transcripts` 目录下：
```
~/Desktop/voice_transcripts/
├── audio/
│   └── recorded_20250627_223757.wav
├── voice_note_20250627_223807.md
└── daily_log_20250627.md
```
- **`audio/`**: 存储所有录音的原始 `.wav` 文件。
- **`voice_note_...`**: 每次转写的独立 Markdown 文件。
- **`daily_log_...`**: 某一天的所有转写稿的合并日志。

</details>

## 🤝 贡献

欢迎任何形式的贡献！无论是报告错误、建议新功能还是提交拉取请求，我们都非常感谢您的帮助。在进行任何重大更改之前，请先开启一个 issue 进行讨论。

未来的开发方向：
- 跨平台支持 (Linux, Windows)，使用环境变量管理 API 密钥。
- 开发 `voice clean` 命令来管理旧的录音和转写稿。
- 支持更多的转写服务。

## 📄 许可证



Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

