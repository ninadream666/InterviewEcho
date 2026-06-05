"""
模块名称：应用全局配置（config）
功能描述：基于 pydantic-settings 的配置管理模块。
从 .env 文件和环境变量中加载所有应用配置项，包括：
- 服务主机/端口
- 数据库连接信息
- LLM（大语言模型）API 密钥与参数
- Whisper 语音识别模型
- Judge0 代码判题服务参数
- CORS 跨域策略
提供全局单例 settings 供其他模块直接引用。
"""

from functools import cached_property
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """应用程序全局配置类。所有配置项通过环境变量或 .env 文件注入。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ========== 服务配置 ==========
    APP_HOST: str = Field(default="127.0.0.1")
    APP_PORT: int = Field(default=8000)

    # ========== 数据库配置 ==========
    DATABASE_URL: Optional[str] = Field(default=None)
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=3306)
    DB_USER: str = Field(default="root")
    DB_PASS: str = Field(default="")
    DB_NAME: str = Field(default="interview_echo")

    # ========== LLM 大语言模型配置 ==========
    LLM_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "DEEPSEEK_API_KEY"),
    )
    LLM_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("LLM_BASE_URL", "DEEPSEEK_BASE_URL"),
    )
    LLM_MODEL: str = Field(
        default="gpt-3.5-turbo-1106",
        validation_alias=AliasChoices("LLM_MODEL", "DEEPSEEK_MODEL"),
    )
    LLM_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("LLM_EMBEDDING_MODEL", "EMBEDDING_MODEL"),
    )

    # ========== 跨域与语音识别配置 ==========
    CORS_ORIGINS: str = Field(default="*")
    WHISPER_MODEL: str = Field(default="small")
    GITHUB_TOKEN: str = Field(default="")

    # ========== Judge0 代码判题服务配置 ==========
    JUDGE0_BASE_URL: str = Field(default="http://127.0.0.1:2358")
    JUDGE0_TIMEOUT_SECONDS: float = Field(default=12)
    JUDGE0_POLL_INTERVAL_SECONDS: float = Field(default=0.6)
    JUDGE0_MAX_POLL_ATTEMPTS: int = Field(default=90)
    CODE_MAX_SOURCE_LENGTH: int = Field(default=20000)
    CODE_MAX_TEST_CASES: int = Field(default=30)
    CODE_MAX_CONCURRENT_JUDGE_CASES: int = Field(default=8)
    CODE_OUTPUT_LIMIT: int = Field(default=4000)

    @cached_property
    def cors_origins(self) -> List[str]:
        """
        解析 CORS 允许的域名列表。

        Returns:
            List[str]: 域名列表，"*" 表示允许所有来源。
        """
        value = (self.CORS_ORIGINS or "*").strip()
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    @cached_property
    def sqlalchemy_database_url(self) -> str:
        """
        构建 SQLAlchemy 数据库连接字符串。
        优先使用 DATABASE_URL（若已配置），否则通过 DB_HOST/DB_PORT 等字段拼接 MySQL 连接串。

        Returns:
            str: SQLAlchemy 格式的数据库 URL。
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()
