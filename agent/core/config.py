import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()

# --- 路径与阈值常量 ---
WORKDIR = Path(os.getcwd())
OUTPUT_STR = r"D:\sandbox"
OUTPUT_DIR = Path(OUTPUT_STR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HOT_STATE_FILE = WORKDIR.parent / ".agent_hot_state.json"
COLD_LOG_FILE = WORKDIR.parent / ".agent_audit.log"
PLAN_FILE = WORKDIR.parent / "PLAN.md"

THRESHOLD_CHARS = 40000 * 4
KEEP_RECENT = 5

# --- LLM 引擎初始化 ---
BASE_URL = os.getenv("API_URL")
BASE_API_KEY = os.getenv("BASE_API_KEY")
BASE_MODEL = os.getenv("BASE_MODEL")
CHILD_API_KEY = os.getenv("CHILD_API_KEY")
CHILD_MODEL = os.getenv("CHILD_MODEL")
# default_headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {API_KEY}",
# }

# 非本地用
# base_llm = ChatOpenAI(
#     api_key=API_KEY or "",
#     model=MODEL,
#     base_url=BASE_URL,
#     temperature=0,
#     default_headers=default_headers,
#     http_client=httpx.Client(
#         proxy=os.getenv("HIS_PROXY", default=None),
#         verify=False,
#     )
# )

# 本地模型用
base_llm = ChatOpenAI(
    api_key=BASE_API_KEY or "",
    model=BASE_MODEL,
    base_url=BASE_URL,
    temperature=0,
    max_retries=2,
    timeout=120.0,
    extra_body={
        "num_ctx": 2048
    }
)

child_llm = ChatOpenAI(
    api_key=CHILD_API_KEY or "",
    model=CHILD_MODEL,
    base_url=BASE_URL,
    temperature=0,
    timeout=120.0,
    extra_body={
        "num_ctx": 2048
    }
)