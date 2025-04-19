# def ToolScanner(services_dir: str) -> List[Callable]:
#     """扫描services目录，收集所有符合规范的工具方法"""
#     tools = []
#     for root, _, files in os.walk(services_dir):
#         for file in files:
#             if file.endswith(".py") and not file.startswith("_"):
#                 module_path = os.path.join(root, file)
#                 module_name = module_path.replace("/", ".").rstrip(".py")
#                 spec = importlib.util.spec_from_file_location(module_name, module_path)
#                 if spec and spec.loader:
#                     module = importlib.util.module_from_spec(spec)
#                     spec.loader.exec_module(module)
#
#                     # 扫描模块中的class
#                     for _, cls in inspect.getmembers(module, inspect.isclass):
#                         for method_name, method in inspect.getmembers(cls, inspect.iscoroutinefunction):
#                             tools.append(method)
#     return tools
import os
import importlib.util
import inspect
from typing import List, Tuple, Callable

from config.logger_config import logger


def ToolScanner(services_dir: str) -> List[Tuple[object, Callable]]:
    """扫描services目录，收集所有符合规范的工具方法（返回(实例,方法)对）"""
    tools = []
    logger.info(f"Tool Scanner Started At {services_dir}")
    for root, _, files in os.walk(services_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                module_path = os.path.join(root, file)
                module_name = module_path.replace("/", ".").rstrip(".py")

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # 扫描模块中的class
                    for _, cls in inspect.getmembers(module, inspect.isclass):
                        # 创建class实例
                        if cls.__module__ != module.__name__:
                            continue
                        try:
                            instance = cls()
                        except Exception as e:
                            logger.warning(f"Failed to instantiate {cls.__name__}: {e}")
                            continue
                        for method_name, method in inspect.getmembers(instance, inspect.iscoroutinefunction):
                            if getattr(method, "__deprecation_warning__", False):
                                logger.info(f"Skip deprecated method {method_name} of class {cls.__name__}")
                                continue
                            if not method_name.startswith("_"):
                                tools.append((instance, method))
    logger.info(f"Tool Scanner Finished, Get Tools: {tools}")
    return tools
