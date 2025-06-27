# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
安全管理模块

提供Keychain密钥管理、文件清理等安全功能。
"""

import os
import subprocess
from typing import Optional
from pathlib import Path


class SecurityManager:
    """安全管理器类，负责密钥管理和安全清理功能"""
    
    def __init__(self) -> None:
        """初始化安全管理器"""
        self.user = os.getenv("USER", "")
    
    def get_deepinfra_token(self) -> str:
        """
        从macOS Keychain获取DeepInfra API密钥
        
        Returns:
            str: API密钥
            
        Raises:
            RuntimeError: 如果无法获取密钥
        """
        try:
            result = subprocess.run(
                [
                    "security", 
                    "find-generic-password",
                    "-a", self.user,
                    "-s", "deepinfra",
                    "-w"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            token = result.stdout.strip()
            if not token:
                raise RuntimeError("DeepInfra token is empty")
            return token
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to retrieve DeepInfra token from Keychain: {e}\n"
                "Please ensure the token is stored with:\n"
                f'security add-generic-password -a "{self.user}" -s "deepinfra" '
                '-w "your-token-here" -T /usr/bin/python3'
            )
    
    def secure_delete_file(self, file_path: Path) -> bool:
        """
        安全删除文件
        
        Args:
            file_path: 要删除的文件路径
            
        Returns:
            bool: 是否成功删除
        """
        try:
            if file_path.exists():
                os.remove(file_path)
                return True
            return False
        except OSError as e:
            print(f"Warning: Failed to delete {file_path}: {e}")
            return False
    
    def validate_api_key(self, token: str) -> bool:
        """
        验证API密钥格式
        
        Args:
            token: API密钥
            
        Returns:
            bool: 是否为有效格式
        """
        # DeepInfra API密钥可能不以sk-开头，只检查长度和基本格式
        return len(token) > 10 and token.strip() != "" 