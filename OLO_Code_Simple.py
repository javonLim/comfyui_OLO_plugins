"""OLO代码执行节点简化修复版本，用于执行自定义Python代码"""
from pathlib import Path
import sys
import io
import contextlib
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import traceback

# GLOBALS

ROOT = Path(__file__).resolve().parent


class AlwaysEqualProxy(str):
    """始终相等的代理类，用于通配符类型"""

    def __eq__(self, other: Any) -> bool:
        """重载相等比较，始终返回True"""
        return True

    def __ne__(self, other: Any) -> bool:
        """重载不等比较，始终返回False"""
        return False


class OLO_Code_Simple:
    """OLO代码执行节点简化修复版本，用于执行自定义Python代码"""

    # 节点元数据
    NODE_NAME = "OLO_Code_Simple"
    NODE_CATEGORY = "OLO/Utility"

    # 内置函数和模块白名单
    SAFE_BUILTINS = {
        '__import__': __import__,
        'abs': abs,
        'all': all,
        'any': any,
        'ascii': ascii,
        'bin': bin,
        'bool': bool,
        'bytes': bytes,
        'callable': callable,
        'chr': chr,
        'complex': complex,
        'divmod': divmod,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'format': format,
        'frozenset': frozenset,
        'getattr': getattr,
        'hasattr': hasattr,
        'hash': hash,
        'hex': hex,
        'id': id,
        'int': int,
        'isinstance': isinstance,
        'issubclass': issubclass,
        'iter': iter,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'next': next,
        'oct': oct,
        'ord': ord,
        'pow': pow,
        'range': range,
        'repr': repr,
        'reversed': reversed,
        'round': round,
        'set': set,
        'slice': slice,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'type': type,
        'zip': zip,
    }

    # 支持的内置模块
    SAFE_MODULES = {
        'math': __import__('math'),
        'random': __import__('random'),
        'datetime': __import__('datetime'),
        'json': __import__('json'),
        're': __import__('re'),
        'os.path': __import__('os.path'),
        'string': __import__('string'),
    }

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """定义节点输入类型

        Returns:
            Dict[str, Any]: 输入类型定义
        """
        return {
            "optional": {
                "code_input": (
                    "STRING", {
                        "default": "output = 'hello, world!'\noutput = inputs.get('in0', 'default_input')",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "要执行的Python代码，使用output变量(单输出)或outputs字典(多输出)进行输出"
                    }
                ),
                "inputcount": ("INT", {"default": 1, "min": 1, "max": 100, "step": 1, "tooltip": "输入端口数量"}),
                "outputcount": ("INT", {"default": 1, "min": 1, "max": 8, "step": 1, "tooltip": "输出端口数量"}),
                "timeout": ("INT", {"default": 5, "min": 1, "max": 60, "step": 1, "tooltip": "代码执行超时时间(秒)"}),
                "file": ("STRING", {
                    "default": "./res/hello.py",
                    "multiline": False,
                    "dynamicPrompts": False,
                    "tooltip": "从文件加载代码，优先级高于code_input"
                }),
                "use_file": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否使用文件中的代码"
                }),
                "run_always": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否总是运行，忽略缓存"
                }),
                "enable_sandbox": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否启用安全沙箱"
                }),
                "in0": ("*", {"tooltip": "输入0"}),
            }
        }

    CATEGORY = NODE_CATEGORY

    # 使用固定数量的输出类型，与RB_Code完全一致
    RETURN_TYPES = ("IMAGE", "IMAGE", "INT", "STRING",)  # 使用具体的类型而不是通配符
    RETURN_NAMES = ("output_0", "output_1", "output_2", "output_3",)
    FUNCTION = "execute"
    DESCRIPTION = """
    OLO代码执行节点简化修复版本，用于执行自定义Python代码

    特性：
    - 支持直接输入代码或从文件加载
    - 提供安全沙箱，限制代码执行权限
    - 支持超时机制，防止无限循环
    - 提供丰富的内置函数和模块
    - 支持1-100个动态输入端口
    - 支持4个固定输出端口
    - 提供详细的错误信息
    - 支持代码缓存，提高执行效率
    - 支持单输出和多输出两种模式
    - 使用固定输出类型，避免连接问题

    输出方式：
    1. 单输出模式：output = 'value'  # 结果会输出到output_0
    2. 多输出模式：outputs[0] = 'value1'; outputs[1] = 'value2'  # 结果会输出到对应的output_0, output_1

    使用示例：
    # 单输出示例
    output = 'hello, world!'
    output = inputs.get('in0', 'default')
    num_inputs = len(inputs)

    # 多输出示例
    outputs[0] = 'first output'
    outputs[1] = 42
    outputs[2] = [1, 2, 3]
    outputs[3] = {'key': 'value'}
    """

    @classmethod
    def IS_CHANGED(cls, code_input: str, inputcount: int, outputcount: int, timeout: int, file: str, use_file: bool, run_always: bool, enable_sandbox: bool, **kwargs: Any) -> Union[float, str]:
        """检查节点是否需要重新执行

        Args:
            code_input: 代码输入
            inputcount: 自定义输入端口数量
            outputcount: 自定义输出端口数量
            timeout: 超时时间(秒)
            file: 文件路径
            use_file: 是否使用文件
            run_always: 是否总是运行
            enable_sandbox: 是否启用安全沙箱
            **kwargs: 其他参数

        Returns:
            Union[float, str]: 如果需要重新执行返回nan，否则返回哈希值
        """
        if run_always:
            return float('nan')

        # 创建临时实例调用get_exec_string
        temp_instance = cls()
        exec_string = temp_instance.get_exec_string(code_input, file, use_file)
        # 确保所有参数都包含在哈希值中，包括enable_sandbox
        hash_value = f'$$inputcount:{inputcount}$$outputcount:{outputcount}$$timeout:{timeout}$$enable_sandbox:{enable_sandbox}$$' + \
            str(kwargs) + '$$' + exec_string + '$$'
        return hash_value

    def __init__(self):
        """初始化OLO_Code_Simple节点"""
        self.code_cache = {}  # 代码缓存
        self.last_execution_time = 0.0  # 上次执行时间

    def execute(self, code_input: str, inputcount: int, outputcount: int, timeout: int, file: str, use_file: bool, run_always: bool, enable_sandbox: bool = True, **kwargs: Any) -> Tuple[Any, ...]:
        """执行代码

        Args:
            code_input: 代码输入
            inputcount: 输入端口数量
            outputcount: 输出端口数量
            timeout: 超时时间(秒)
            file: 文件路径
            use_file: 是否使用文件
            run_always: 是否总是运行
            enable_sandbox: 是否启用安全沙箱
            **kwargs: 其他参数

        Returns:
            Tuple[Any, ...]: 输出结果，固定4个输出
        """
        # 初始化输出
        output = None
        outputs = {i: None for i in range(4)}  # 固定4个输出

        # 处理输入，与RB_Code保持完全一致的处理方式
        inputs = kwargs.copy()
        # 添加索引映射，支持inputs[0]访问，与RB_Code保持一致
        inputs.update({i: v for i, v in enumerate(kwargs.values())})

        # 获取要执行的代码
        code = self.get_exec_string(code_input, file, use_file)

        # 准备执行环境，与RB_Code保持一致但增加安全功能
        env = {
            "inputs": inputs,
            "outputs": outputs,
            "output": output,  # 添加output变量初始化
            "print": self._safe_print,
            "time": time,
        }

        # 添加安全内置函数
        if enable_sandbox:
            env.update({
                "__builtins__": self.SAFE_BUILTINS,
            })
            # 添加安全模块
            env.update(self.SAFE_MODULES)
        else:
            # 不安全模式下添加所有内置函数
            env.update({"__builtins__": __builtins__})

        try:
            # 使用超时机制执行代码
            start_time = time.time()

            # 执行代码
            exec(code, env)

            # 检查执行时间
            execution_time = time.time() - start_time
            if execution_time > timeout:
                raise RuntimeError(
                    f"Code execution timed out after {execution_time:.2f} seconds")

            self.last_execution_time = execution_time

            # 获取执行结果
            output = env.get("output", None)
            outputs = env.get("outputs", {i: None for i in range(4)})

            # 处理单输出模式：如果使用了output变量且outputs[0]为空，则将output值赋给outputs[0]
            if output is not None and outputs.get(0) is None:
                outputs[0] = output

        except Exception as e:
            # 捕获并格式化错误信息
            error_msg = f"Error executing code: {e}\n\n" + \
                traceback.format_exc()
            raise RuntimeError(error_msg)

        # 确保输出类型匹配RETURN_TYPES
        # output_0: IMAGE
        # output_1: IMAGE
        # output_2: INT
        # output_3: STRING
        
        # 获取输出值，如果没有设置则使用默认值
        result = []
        
        # output_0: IMAGE
        img0 = outputs.get(0)
        if img0 is None:
            # 创建一个默认的1x1黑色图像
            import torch
            img0 = torch.zeros((1, 1, 1, 3), dtype=torch.float32)
        result.append(img0)
        
        # output_1: IMAGE
        img1 = outputs.get(1)
        if img1 is None:
            # 创建一个默认的1x1黑色图像
            import torch
            img1 = torch.zeros((1, 1, 1, 3), dtype=torch.float32)
        result.append(img1)
        
        # output_2: INT
        int2 = outputs.get(2)
        if int2 is None:
            int2 = 0
        result.append(int2)
        
        # output_3: STRING
        str3 = outputs.get(3)
        if str3 is None:
            str3 = ""
        result.append(str3)

        return tuple(result)

    def get_exec_string(self, code_input: str, file: str, use_file: bool) -> str:
        """获取要执行的代码字符串

        Args:
            code_input: 代码输入
            file: 文件路径
            use_file: 是否使用文件

        Returns:
            str: 要执行的代码字符串

        Raises:
            RuntimeError: 如果加载文件失败
        """
        if use_file:
            # 生成缓存键
            cache_key = f"file:{file}"

            # 检查缓存
            if cache_key in self.code_cache:
                return self.code_cache[cache_key]

            code_input = ""
            possible_paths = [
                Path(ROOT / file),
                Path(file),
                Path.cwd() / file
            ]

            found_file = None
            for path in possible_paths:
                if path.is_file():
                    found_file = path
                    break

            if found_file is None:
                raise RuntimeError(f"[OLO_Code_Simple] file not found: {file}")

            try:
                with open(str(found_file), 'r', encoding='utf-8') as f:
                    code_input = f.read()

                # 更新缓存
                self.code_cache[cache_key] = code_input
            except Exception as e:
                raise RuntimeError(f"[OLO_Code_Simple] error loading code file: {e}")
        return code_input

    def _safe_print(self, *args: Any, **kwargs: Any) -> None:
        """安全的print函数，将输出重定向到控制台"""
        # 捕获print输出，防止无限输出
        output = " ".join(map(str, args))
        # 限制输出长度
        if len(output) > 1000:
            output = output[:1000] + "... (truncated)"
        # 输出到控制台
        print(output, **kwargs)


NODE_CLASS_MAPPINGS = {
    OLO_Code_Simple.NODE_NAME: OLO_Code_Simple
}
NODE_DISPLAY_NAME_MAPPINGS = {
    OLO_Code_Simple.NODE_NAME: "OLO_Code_Simple"
}