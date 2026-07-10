"""Encryption Providers — 加密存储实现 (P6-5)

支持两种加密方式:
1. FileEncryptionProvider: 开发环境，使用 Fernet 对称加密
2. CloudEncryptionProvider: 生产环境，使用云端 Secret Manager

加密密钥管理:
- 环境变量: SECRET_ENCRYPTION_KEY
- 文件: governance/.data/.secret_key
- 自动生成: 首次运行时生成并保存
"""

import os
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class EncryptionProvider:
    """加密 Provider 基类"""

    def encrypt(self, plaintext: str) -> str:
        """加密明文，返回密文字符串"""
        raise NotImplementedError

    def decrypt(self, ciphertext: str) -> str:
        """解密密文，返回明文字符串"""
        raise NotImplementedError


class FileEncryptionProvider(EncryptionProvider):
    """文件加密 Provider — 使用 Fernet 对称加密

    密钥优先级:
    1. 环境变量 SECRET_ENCRYPTION_KEY
    2. 文件 governance/.data/.secret_key
    3. 自动生成新密钥
    """

    def __init__(self, key_path: Optional[str] = None):
        """初始化加密 Provider

        Args:
            key_path: 密钥文件路径（默认: governance/.data/.secret_key）
        """
        if key_path is None:
            key_path = self._get_default_key_path()

        self.key_path = Path(key_path)
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)

        logger.info(f"FileEncryptionProvider initialized (key_path={self.key_path})")

    def encrypt(self, plaintext: str) -> str:
        """加密明文，返回 base64 编码的密文"""
        if not plaintext:
            return ""

        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """解密密文，返回明文"""
        if not ciphertext:
            return ""

        try:
            decrypted_bytes = self.fernet.decrypt(ciphertext.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {e}")

    def _load_or_generate_key(self) -> bytes:
        """加载或生成加密密钥

        优先级:
        1. 环境变量 SECRET_ENCRYPTION_KEY
        2. 文件 self.key_path
        3. 生成新密钥并保存到 self.key_path

        Returns:
            bytes: Fernet 密钥（32 字节 base64 编码）
        """
        # 优先级 1: 环境变量
        env_key = os.getenv("SECRET_ENCRYPTION_KEY")
        if env_key:
            logger.info("Using encryption key from SECRET_ENCRYPTION_KEY")
            return env_key.encode('utf-8')

        # 优先级 2: 文件
        if self.key_path.exists():
            logger.info(f"Loading encryption key from {self.key_path}")
            return self.key_path.read_bytes()

        # 优先级 3: 生成新密钥
        logger.warning(f"Generating new encryption key at {self.key_path}")
        new_key = Fernet.generate_key()

        # 保存到文件
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        self.key_path.write_bytes(new_key)

        # 设置文件权限（仅所有者可读写）
        try:
            os.chmod(self.key_path, 0o600)
        except Exception as e:
            logger.warning(f"Failed to set key file permissions: {e}")

        logger.info(f"Encryption key saved to {self.key_path}")
        logger.warning("⚠️  Please backup this key securely! Loss of this key means loss of all encrypted data.")

        return new_key

    @staticmethod
    def _get_default_key_path() -> str:
        """获取默认密钥路径"""
        # 尝试从项目根目录定位
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "governance" / ".data" / ".secret_key")


class CloudEncryptionProvider(EncryptionProvider):
    """云端加密 Provider — 支持 AWS/Azure/Vault/GCP

    注意: 这是占位实现，实际生产环境需要集成真实的云服务 SDK
    """

    def __init__(self, provider: str, config: dict):
        """初始化云端加密 Provider

        Args:
            provider: 云服务类型 ("aws" | "azure" | "vault" | "gcp")
            config: 云服务配置（如 region, credentials 等）
        """
        self.provider = provider
        self.config = config
        self.client = self._init_client()

        logger.info(f"CloudEncryptionProvider initialized (provider={provider})")

    def encrypt(self, plaintext: str) -> str:
        """云端加密（占位实现）

        实际生产中，云端 Secret Manager 通常不在本地加密，
        而是直接存储明文到云端，由云服务负责加密。

        这里返回原文作为占位。
        """
        logger.warning("CloudEncryptionProvider.encrypt() is a placeholder")
        return plaintext

    def decrypt(self, ciphertext: str) -> str:
        """云端解密（占位实现）

        实际生产中，应该调用云服务 SDK 获取 Secret 值。

        这里返回原文作为占位。
        """
        logger.warning("CloudEncryptionProvider.decrypt() is a placeholder")
        return ciphertext

    def _init_client(self):
        """初始化云服务客户端（占位实现）"""
        if self.provider == "aws":
            # TODO: import boto3
            # return boto3.client('secretsmanager', **self.config)
            logger.warning("AWS Secrets Manager client not implemented")
            return None
        elif self.provider == "azure":
            # TODO: from azure.keyvault.secrets import SecretClient
            # return SecretClient(**self.config)
            logger.warning("Azure Key Vault client not implemented")
            return None
        elif self.provider == "vault":
            # TODO: import hvac
            # return hvac.Client(**self.config)
            logger.warning("HashiCorp Vault client not implemented")
            return None
        elif self.provider == "gcp":
            # TODO: from google.cloud import secretmanager
            # return secretmanager.SecretManagerServiceClient(**self.config)
            logger.warning("GCP Secret Manager client not implemented")
            return None
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}")


# 全局单例
_encryption_provider: Optional[EncryptionProvider] = None


def get_encryption_provider(
    provider_type: str = "file",
    **kwargs
) -> EncryptionProvider:
    """获取加密 Provider（单例模式）

    Args:
        provider_type: "file" | "cloud"
        **kwargs: Provider 特定参数
            - file: key_path (可选)
            - cloud: provider ("aws" | "azure" | "vault" | "gcp"), config (dict)

    Returns:
        EncryptionProvider 实例
    """
    global _encryption_provider

    if _encryption_provider is None:
        if provider_type == "file":
            key_path = kwargs.get("key_path")
            _encryption_provider = FileEncryptionProvider(key_path=key_path)
        elif provider_type == "cloud":
            cloud_provider = kwargs.get("provider", "aws")
            config = kwargs.get("config", {})
            _encryption_provider = CloudEncryptionProvider(cloud_provider, config)
        else:
            raise ValueError(f"Unsupported provider_type: {provider_type}")

    return _encryption_provider


def reset_encryption_provider():
    """重置全局 Provider（用于测试）"""
    global _encryption_provider
    _encryption_provider = None
