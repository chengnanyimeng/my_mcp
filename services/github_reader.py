import base64
import json
import aiohttp
import asyncio
import time
from typing import List, Dict, Any

from config.logger_config import logger
from utils.misc import Deprecated

class GithubService:
    BASE_URL = "https://api.github.com"
    TIMEOUT = 10
    RETRY = 3
    CACHE_TTL = 300  # 5分钟缓存

    def __init__(self):
        self._cache = {}  # (url, branch) -> (timestamp, data)

    async def _fetch(self, url: str, headers=None) -> Any:
        """带超时和重试的请求"""
        for attempt in range(1, self.RETRY + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"Request failed: {url} with status {response.status}")
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                logger.error(f"[Attempt {attempt}] Error fetching {url}: {e}")
                if attempt == self.RETRY:
                    logger.error(f"Failed after {self.RETRY} retries for {url}")
                    raise
                await asyncio.sleep(1)

    def _is_cache_valid(self, key: str) -> bool:
        return key in self._cache and (time.time() - self._cache[key][0]) < self.CACHE_TTL

    def _response_wrap(self, content: str) -> List[Dict]:
        """TEXT response wrapper"""
        #todo: need to support other type returns including audio & image & resource
        return  [{"type": "text", "text": content}]


    async def read_repo_info(self, repo_full_name: str) -> List[dict]:
        """获取仓库基本信息"""
        url = f"{self.BASE_URL}/repos/{repo_full_name}"
        if self._is_cache_valid(url):
            return [
                    {"type": "text", "text": self._cache[url][1]}
                ]


        try:
            logger.info("action=read_repo_info, url=%s", url)
            data = await self._fetch(url)
            result = {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "html_url": data.get("html_url"),
            }
            self._cache[url] = (time.time(), json.dumps(result))
            logger.info("action=read_repo_info, result=%s", json.dumps(result))
            return self._response_wrap(json.dumps(result))

        except Exception as e:
            logger.error(f"Failed to read repo info for {repo_full_name}: {e}")
            return self._response_wrap(str(e))

    async def list_repo_tree(self, repo_full_name: str, branch: str = "main") -> List[Dict]:
        """列出仓库目录树"""
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}/git/trees/{branch}?recursive=1"
            if self._is_cache_valid(url):
                return self._cache[url][1]

            data = await self._fetch(url)
            tree = data.get("tree", [])

            # 过滤掉非法的元素，比如 path 不是字符串的
            tree = [item for item in tree if isinstance(item.get("path"), str)]

            self._cache[url] = (time.time(), json.dumps(tree))
            return self._response_wrap(json.dumps(tree))
        except Exception as e:
            logger.error(f"Failed to read repo tree for {repo_full_name}: {e}")
            return self._response_wrap(str(e))

    async def read_file_content(self, repo_full_name: str, path: str, branch: str = "main") -> dict[str, str] | list[
        dict] | Any:
        """读取单个文件内容，兼容文本/二进制"""
        url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{path}?ref={branch}"
        headers = {"Accept": "application/vnd.github.v3.raw"}
        cache_key = f"{url}-raw"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][1]

        for attempt in range(1, self.RETRY + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            raw_bytes = await response.read()
                            try:
                                # 优先尝试解成utf-8文本
                                text = raw_bytes.decode("utf-8")
                                content = {
                                    "is_binary": False,
                                    "content": text
                                }
                            except UnicodeDecodeError:
                                # 否则用base64编码二进制
                                content = {
                                    "is_binary": True,
                                    "content": base64.b64encode(raw_bytes).decode("utf-8")
                                }
                            self._cache[cache_key] = (time.time(), content)
                            return {"path": path, **content}
                        else:
                            logger.error(f"Request failed: {url} with status {response.status}")
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                logger.error(f"[Attempt {attempt}] Error reading file {path} in {repo_full_name}@{branch}: {e}")
                if attempt == self.RETRY:
                    logger.error(f"Failed after {self.RETRY} retries reading {path}")
                    return self._response_wrap(json.dumps({"path": path, "error": f"Failed after retries: {str(e)}"}))
                await asyncio.sleep(1)

    @Deprecated
    async def download_repo_structure_with_content(self, repo_full_name: str, branch: str = "main") -> Dict[str, Any]:
        """拉取整个repo的文件结构和内容"""
        result = {}
        try:
            tree = await self.list_repo_tree(repo_full_name, branch)
            for item in tree:
                if item.get("type") == "blob":
                    file_path = item.get("path")
                    file_content = await self.read_file_content(repo_full_name, file_path, branch)
                    self._insert_into_structure(result, file_path.split("/"), file_content.get("content", ""))
            return result
        except Exception as e:
            logger.error(f"Failed to download repo {repo_full_name} structure: {e}")
            return {"error": str(e)}

    def _insert_into_structure(self, structure: dict, path_parts: List[str], content: str):
        """递归插入文件到结构"""
        if len(path_parts) == 1:
            structure[path_parts[0]] = content
        else:
            folder = path_parts[0]
            if folder not in structure:
                structure[folder] = {}
            self._insert_into_structure(structure[folder], path_parts[1:], content)
