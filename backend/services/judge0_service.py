"""
模块名称：Judge0 代码判题服务（judge0_service）
功能描述：封装对 Judge0 代码判题 API 的异步调用。

Judge0 是一个开源的在线代码执行引擎，支持 Python、Java、C++、JavaScript 等语言。
本模块使用 Judge0 的 REST API（提交 + 轮询模式）来执行代码并获取结果。

核心职责：
1. 语言 ID 映射（Python → 71, Java → 62, C++ → 54, JavaScript → 63）
2. 异步提交代码到 Judge0 并轮询结果
3. 输出处理（Base64 解码、截断、换行符统一）

异常处理：
- Judge0 不可用时抛出 Judge0Unavailable 异常，调用方应 catch 并向用户展示友好提示。
"""

import asyncio
import base64
from dataclasses import dataclass
from typing import Optional

import httpx

from core.config import settings


# ============================================================
# 常量定义
# ============================================================

# Judge0 语言 ID 映射表
LANGUAGE_IDS = {
    "python": 71,
    "java": 62,
    "cpp": 54,
    "javascript": 63,
}

# Judge0 状态码含义：
#   1: In Queue, 2: Processing → 运行中
#   3: Accepted → 执行成功（需比对输出判断是否通过）
#   4: Wrong Answer → 输出不匹配（Judge0 自带的比对，我们未使用，自己做比对）
#   5: Time Limit Exceeded
#   6: Compilation Error
#   7-12: Runtime Error (SIGSEGV, SIGXFSZ, etc.)
#   13: Internal Error
RUNNING_STATUS_IDS = {1, 2}       # 仍在队列或执行中
COMPILE_ERROR_STATUS_IDS = {6}    # 编译错误
TIME_LIMIT_STATUS_IDS = {5}       # 超时


class Judge0Unavailable(Exception):
    """Judge0 服务不可用时抛出的异常。"""
    pass


# ============================================================
# 结果数据类
# ============================================================

@dataclass
class Judge0Result:
    """
    Judge0 判题结果。

    字段说明：
    - status_id: Judge0 返回的状态码（1-13）
    - status_description: 状态描述文本
    - stdout: 程序标准输出
    - stderr: 程序标准错误
    - compile_output: 编译错误信息
    - time: 运行耗时（秒）
    - memory: 内存使用（KB）
    """
    status_id: int
    status_description: str
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    time: Optional[float] = None
    memory: Optional[int] = None
    message: str = ""

    @property
    def raw_status(self) -> str:
        """将 status_id 转换为人类可读的状态字符串。"""
        if self.status_id == 3:
            return "Finished"
        if self.status_id in COMPILE_ERROR_STATUS_IDS:
            return "Compile Error"
        if self.status_id in TIME_LIMIT_STATUS_IDS:
            return "Time Limit Exceeded"
        if self.status_id == 4:
            return "Wrong Answer"
        if self.status_id >= 7:
            return "Runtime Error"
        return self.status_description or "Judge Error"


# ============================================================
# 文本处理辅助函数
# ============================================================

def trim_output(value: Optional[str]) -> str:
    """
    统一换行符并去除首尾空白。

    处理 Judge0 返回的输出中可能混用 \\r\\n 和 \\r 的情况。
    """
    if not value:
        return ""
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def truncate_text(value: Optional[str], limit: Optional[int] = None) -> str:
    """
    截断文本到指定长度，超出部分添加 "[truncated]" 标记。

    用于防止异常大的输出撑爆数据库字段或 LLM prompt。
    """
    if not value:
        return ""
    limit = limit or settings.CODE_OUTPUT_LIMIT
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"


def decode_judge0_text(value: Optional[str]) -> str:
    """
    Base64 解码 Judge0 返回的文本字段。

    Judge0 在 base64_encoded=true 模式下返回 Base64 编码的 stdout/stderr 等字段。
    """
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


# ============================================================
# Judge0 服务类
# ============================================================

class Judge0Service:
    """
    Judge0 代码判题服务客户端。

    使用方式：
        judge0_service = Judge0Service()
        result = await judge0_service.run_code("python", "print(1+1)", "")

    工作流程：
    1. POST /submissions 提交代码（wait=false，异步模式）
    2. GET /submissions/{token} 轮询直到状态不再是 Running
    3. 解析并返回 Judge0Result
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.JUDGE0_BASE_URL).rstrip("/")
        self.timeout = settings.JUDGE0_TIMEOUT_SECONDS
        self.poll_interval = settings.JUDGE0_POLL_INTERVAL_SECONDS
        self.max_poll_attempts = settings.JUDGE0_MAX_POLL_ATTEMPTS

    async def run_code(self, language: str, source_code: str, stdin: str) -> Judge0Result:
        """
        提交代码到 Judge0 并等待判题结果。

        Args:
            language: 编程语言标识（"python" / "java" / "cpp" / "javascript"）。
            source_code: 完整源代码。
            stdin: 标准输入内容。

        Returns:
            Judge0Result: 判题结果。

        Raises:
            ValueError: 不支持的语言。
            Judge0Unavailable: Judge0 服务不可达或请求超时。
        """
        language_id = LANGUAGE_IDS.get(language)
        if not language_id:
            raise ValueError("Unsupported language")

        # 构造判题请求
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "stdin": stdin,
            "cpu_time_limit": 2,
            "wall_time_limit": 6,
            "memory_limit": 128000,
            "max_processes_and_or_threads": 64,
            "enable_network": False,
        }
        # C++ 和 Java 编译较慢，放宽时间限制
        if language in {"cpp", "java"}:
            payload.update(
                {
                    "cpu_time_limit": 4,
                    "wall_time_limit": 12,
                    "memory_limit": 256000,
                }
            )

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, trust_env=False) as client:
                # 1. 提交代码（异步模式：wait=false）
                create_resp = await client.post("/submissions", params={"base64_encoded": "false", "wait": "false"}, json=payload)
                create_resp.raise_for_status()
                token = create_resp.json().get("token")
                if not token:
                    raise Judge0Unavailable("Judge0 did not return a submission token.")

                # 2. 轮询判题结果
                fields = "stdout,stderr,compile_output,message,status,time,memory"
                for _ in range(self.max_poll_attempts):
                    result_resp = await client.get(
                        f"/submissions/{token}",
                        params={"base64_encoded": "true", "fields": fields},
                    )
                    result_resp.raise_for_status()
                    data = result_resp.json()
                    status = data.get("status") or {}
                    status_id = int(status.get("id") or 0)
                    if status_id not in RUNNING_STATUS_IDS:
                        # 判题完成，构造结果对象
                        return Judge0Result(
                            status_id=status_id,
                            status_description=status.get("description") or "Unknown",
                            stdout=truncate_text(decode_judge0_text(data.get("stdout"))),
                            stderr=truncate_text(decode_judge0_text(data.get("stderr"))),
                            compile_output=truncate_text(decode_judge0_text(data.get("compile_output"))),
                            message=truncate_text(decode_judge0_text(data.get("message"))),
                            time=float(data["time"]) if data.get("time") not in (None, "") else None,
                            memory=int(data["memory"]) if data.get("memory") not in (None, "") else None,
                        )
                    await asyncio.sleep(self.poll_interval)

        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
            raise Judge0Unavailable(
                f"Judge0 service is unavailable at {self.base_url}. "
                "Start Docker Judge0 or set JUDGE0_BASE_URL correctly."
            ) from exc

        # 轮询超时，视为 Time Limit Exceeded
        return Judge0Result(
            status_id=5,
            status_description="Time Limit Exceeded",
            message="Judge0 polling timed out.",
        )


# 全局单例
judge0_service = Judge0Service()
