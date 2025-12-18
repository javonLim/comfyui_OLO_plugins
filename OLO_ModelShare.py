# -*- coding: utf-8 -*-
import os
import sys
import configparser
import shutil
import subprocess
import ctypes

# 初始化统计变量
success_count = 0
skip_count = 0
error_count = 0

# 日志级别常量
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# 当前日志级别
current_log_level = LOG_LEVELS['INFO']  # 默认INFO级别

# 定义一个安全的打印函数，处理中文编码问题


def safe_print(message):
    """
    安全打印函数，处理中文编码问题

    参数:
        message: 要打印的消息
    """
    try:
        # 尝试直接打印
        print(str(message), flush=True)
    except UnicodeEncodeError:
        # 如果遇到编码错误，尝试用utf-8编码再解码
        try:
            safe_message = str(message).encode(
                'utf-8', 'replace').decode('utf-8', 'replace')
            print(safe_message, flush=True)
        except Exception:
            # 最后的备选方案
            print("[消息输出失败]", flush=True)

# 设置日志级别函数


def set_log_level(level):
    """
    设置全局日志级别

    参数:
        level: 日志级别字符串，如 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    """
    global current_log_level
    if level in LOG_LEVELS:
        current_log_level = LOG_LEVELS[level]
        # 使用普通打印确保无论设置什么日志级别都能看到日志级别设置的消息
        safe_print(f"[INFO] 日志级别设置为: {level}")
    else:
        safe_print(f"[WARNING] 无效的日志级别: {level}，使用默认级别: INFO")
        current_log_level = LOG_LEVELS['INFO']

# 根据日志级别安全打印日志


def safe_print_log(level, message):
    """
    根据当前设置的日志级别打印日志消息

    参数:
        level: 日志级别字符串（大写）
        message: 日志消息内容
    """
    if level in LOG_LEVELS and LOG_LEVELS[level] >= current_log_level:
        safe_print(f"[{level}] {message}")


def create_symbolic_links(source_folder, target_folder):
    """
    创建符号链接

    参数:
        source_folder: 源文件夹路径
        target_folder: 目标文件夹路径
    """
    # 声明使用全局变量
    global success_count, skip_count, error_count

    if not os.path.exists(target_folder):
        os.mkdir(target_folder)
    # 获取源文件夹中的所有文件
    files = os.listdir(source_folder)
    # 遍历每个文件，并创建符号链接到目标文件夹
    for file in files:
        source_path = os.path.join(source_folder, file)
        target_path = os.path.join(target_folder, file)
        # 检查目标路径是否已经存在
        if os.path.lexists(target_path):
            if os.path.isdir(target_path):
                create_symbolic_links(source_path, target_path)
            else:
                # 使用safe_print_log根据日志级别过滤输出
                safe_print_log("INFO", f"目标文件{str(target_path)}已存在，跳过创建符号链接")
                skip_count += 1  # 更新跳过计数
                continue

        if os.path.isdir(source_path):
            create_junction(source_path, target_path)
            # 注意：success_count会在create_junction函数中更新
            # 使用safe_print确保中文正确显示
            safe_print_log(
                "INFO", f"创建目录链接成功: {str(file)} 源路径: {str(source_path)} 目标路径: {str(target_path)}")
        else:
            # 创建符号链接
            try:
                os.symlink(source_path, target_path,
                           os.path.isdir(source_path))
                success_count += 1  # 更新成功计数
                # 使用safe_print确保中文正确显示
                safe_print_log("INFO", f"创建符号链接成功: {str(target_path)}")
            except OSError as e:
                error_count += 1  # 更新错误计数
                try:
                    safe_error = str(e).encode(
                        'utf-8', 'replace').decode('utf-8', 'replace')
                    safe_source_path = str(source_path).encode(
                        'utf-8', 'replace').decode('utf-8', 'replace')
                    safe_print_log(
                        "WARNING", f"{safe_error}--符号链接创建失败: {safe_source_path}, 如果是Windows系统，请开启开发者模式后重试")
                except Exception:
                    print("[WARNING] 符号链接创建失败，请开启开发者模式后重试", flush=True)
            except Exception as e:
                error_count += 1  # 更新错误计数
                safe_print_log("ERROR", f"{str(e)}--发生了意外异常")


def create_junction(src, dst):
    """
    创建目录链接（junction）

    参数:
        src: 源路径
        dst: 目标路径
    """
    # 声明使用全局变量
    global success_count, error_count

    import platform
    if platform.system() == "Windows":
        with open(os.devnull, 'w', encoding='utf-8') as devnull:
            try:
                # 使用CREATE_NO_WINDOW标志防止弹出命令窗口
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # 确保路径字符串正确编码
                src_str = str(src).encode(
                    'utf-8', 'replace').decode('utf-8', 'replace')
                dst_str = str(dst).encode(
                    'utf-8', 'replace').decode('utf-8', 'replace')
                # 使用utf-8编码来处理命令行参数
                subprocess.call('cmd.exe /c mklink /J "%s" "%s"' %
                                (dst_str, src_str), shell=True, stdout=devnull, stderr=devnull,
                                startupinfo=startupinfo)
                success_count += 1  # 更新成功计数
                # 使用safe_print确保中文正确显示
                safe_print_log("INFO", f"创建目录链接成功: {src_str} -> {dst_str}")
            except Exception as e:
                error_count += 1  # 更新错误计数
                safe_print_log("ERROR", f"{str(e)}")
    else:
        # 创建符号链接
        try:
            os.symlink(src, dst, os.path.isdir(src))
            success_count += 1  # 更新成功计数
            safe_print_log("INFO", f"创建符号链接成功: {str(src)}")
        except OSError as e:
            error_count += 1  # 更新错误计数
            safe_print_log(
                "WARNING", f"{str(e)}--符号链接创建失败: {str(src)}, 如果是Windows系统，请开启开发者模式后重试")
        except Exception as e:
            error_count += 1  # 更新错误计数
            try:
                safe_error = str(e).encode(
                    'utf-8', 'replace').decode('utf-8', 'replace')
                safe_print_log("ERROR", f"{safe_error}--发生了意外异常")
            except Exception:
                print("[ERROR] 发生了意外异常", flush=True)


def move_files(src, dst):
    """
    移动文件

    参数:
        src: 源目录
        dst: 目标目录
    """
    # 声明使用全局变量
    global success_count, skip_count, error_count

    # 移动src目录下的所有文件到dst目录
    for file_name in os.listdir(src):
        src_file = os.path.join(src, file_name)
        dst_file = os.path.join(dst, file_name)
        # 如果目标文件存在，则跳过
        if os.path.exists(dst_file):
            skip_count += 1  # 更新跳过计数
            continue
        # 移动文件
        try:
            shutil.move(src_file, dst_file)
            success_count += 1  # 更新成功计数
            # 使用safe_print_log根据日志级别过滤输出
            safe_print_log("INFO", f"移动文件: {str(src_file)} -> {str(dst_file)}")
        except Exception as e:
            error_count += 1  # 更新错误计数
            # 使用safe_print_log根据日志级别过滤输出
            safe_print_log(
                "ERROR", f"移动文件失败: {str(src_file)} -> {str(dst_file)}, 错误: {str(e)}")
    # 删除src目录
    try:
        shutil.rmtree(src)
        # 使用safe_print_log根据日志级别过滤输出
        safe_print_log("INFO", f"删除目录: {str(src)}")
    except Exception as e:
        # 使用safe_print_log根据日志级别过滤输出
        safe_print_log("ERROR", f"删除目录失败: {str(src)}, 错误: {str(e)}")

# 获取根目录


def get_root_path():
    """
    获取ComfyUI根目录

    返回:
        str: 根目录路径
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 向上遍历找到ComfyUI根目录
    while True:
        # 检查当前目录是否包含main.py（更宽松的条件，确保能找到正确的根目录）
        if os.path.exists(os.path.join(current_dir, "main.py")):
            return current_dir
        # 获取父目录
        parent_dir = os.path.dirname(current_dir)
        # 如果已经到达根目录，返回当前目录
        if parent_dir == current_dir:
            return current_dir
        # 更新当前目录
        current_dir = parent_dir


# 获取comfyui模型目录
root_path = get_root_path()
folder_path = os.path.join(root_path, "models")

# 使用safe_print_log根据日志级别过滤输出
safe_print_log("INFO", f"识别到comfyui模型目录为：{str(folder_path)}")

# 创建一个ConfigParser对象，支持UTF-8编码
config = configparser.ConfigParser()

# 配置文件路径列表
config_paths = [
    os.path.join(root_path, "custom_nodes",
                 "ComfyUI-OLO_plugins", "shared_config.conf"),
    os.path.join(root_path, "custom_nodes", "shared_config.conf"),
    os.path.join(os.path.dirname(root_path), "shared_config.conf")
]

# 遍历配置文件路径，找到第一个有效的配置文件
for path in config_paths:
    if os.path.exists(path) and os.path.isfile(path):  # 检查文件是否存在且为文件
        try:
            # 尝试加载配置文件，确保使用正确的编码
            config.read(path, encoding='utf-8')
            # 使用safe_print_log根据日志级别过滤输出
            safe_print_log("INFO", f"成功加载配置文件：{str(path)}")

            # 检查是否包含'share_model'部分
            if config.has_section('share_model'):
                # 获取配置项，设置默认值
                # 检查是否有enable配置项，默认为true
                enable = config.getboolean(
                    'share_model', 'enable', fallback=True)
                if not enable:
                    safe_print_log("INFO", "模型共享功能已禁用")
                    break

                share_mode = config.get(
                    'share_model', 'mode', fallback='merge')
                ext_models_path = config.get(
                    'share_model', 'ext_models_path', fallback='')
                log_level = config.get(
                    'share_model', 'log_level', fallback='INFO')

                # 设置日志级别
                set_log_level(log_level)

                # 使用safe_print_log根据日志级别过滤输出
                safe_print_log("INFO", f"当前已开启模型共享，模式为：{str(share_mode)}")
                safe_print_log("INFO", f"拓展模型目录：{str(ext_models_path)}")

                # 检查目标路径是否已经存在
                if os.path.lexists(ext_models_path):
                    if share_mode == "merge":
                        # 使用safe_print_log根据日志级别过滤输出
                        safe_print_log("INFO", "开始创建符号链接...")
                        create_symbolic_links(ext_models_path, folder_path)
                    elif share_mode == "move":
                        # 使用safe_print_log根据日志级别过滤输出
                        safe_print_log("INFO", "开始移动文件...")
                        move_files(folder_path, ext_models_path)
                        safe_print_log("INFO", "开始创建目录链接...")
                        create_junction(ext_models_path, folder_path)
                else:
                    # 使用safe_print_log根据日志级别过滤输出
                    safe_print_log(
                        "ERROR", f"拓展模型目录未找到：{str(ext_models_path)}，配置模型共享失败！请在整合包目录下的shared_config.conf中进行配置！")

                break  # 如果找到有效的配置文件并处理完毕，则停止搜索
        except Exception as e:
            # 使用safe_print_log根据日志级别过滤输出
            safe_print_log("ERROR", f"加载 {str(path)} 时出错：{str(e)}")
    else:
        # 使用safe_print_log根据日志级别过滤输出
        safe_print_log("WARNING", f"配置文件 {str(path)} 不存在或不是文件")

# 检查是否找到了有效的配置文件
if not config.sections():
    # 如果没有找到有效的配置文件，创建默认配置文件
    default_config_path = os.path.join(
        root_path, "custom_nodes", "ComfyUI-OLO_plugins", "shared_config.conf")
    default_config = """
[share_model]
enable = true
# 模式: merge（合并，创建符号链接）或 move（移动，将模型移动到外部目录并创建目录链接）
mode = merge
# 拓展模型目录路径，需要替换为实际路径
ext_models_path =
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = INFO
"""
    try:
        with open(default_config_path, 'w', encoding='utf-8') as f:
            f.write(default_config)
        # 使用safe_print_log根据日志级别过滤输出
        safe_print_log(
            "INFO", f"已创建默认配置文件: {str(default_config_path)}，请根据需要修改配置")
    except Exception as e:
        # 使用safe_print_log根据日志级别过滤输出
        safe_print_log("ERROR", f"创建默认配置文件时发生错误: {str(e)}")

# 输出符号链接创建的统计结果 - 使用INFO级别确保总是显示统计信息
safe_print_log("INFO", "===== 符号链接创建统计结果 =====")
safe_print_log("INFO", f"成功创建的符号链接/目录: {success_count} 个")
safe_print_log("INFO", f"跳过的文件/目录: {skip_count} 个")
safe_print_log("INFO", f"创建失败的符号链接/目录: {error_count} 个")
safe_print_log("INFO", f"总计处理: {success_count + skip_count + error_count} 个项目")
safe_print_log("INFO", "===============================")

# 添加必要的节点映射以符合 ComfyUI 自定义节点规范
# 由于这是一个工具脚本而非UI节点，所以映射为空
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
