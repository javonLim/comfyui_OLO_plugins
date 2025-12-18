MY_CATEGORY = "OLO/Audio"

try:
    import torch
except ImportError:
    # 确保在 ComfyUI 环境中 torch 可用
    raise ImportError(
        "PyTorch (torch) is required for audio processing nodes but was not found.")


class OLO_AudioInfo(object):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("audio_info_string",)
    FUNCTION = "execute"
    CATEGORY = MY_CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = "显示音频的详细信息，包括采样率、长度、通道数等"

    def execute(self, audio):
        """
        执行音频信息提取操作

        参数:
            audio: 音频对象

        返回:
            音频信息字符串
        """
        # 提取音频信息
        sample_rate = audio["sample_rate"]
        waveform = audio["waveform"]

        # 获取波形的形状信息
        # 假设波形的形状为 [Batch, Channels, Samples]
        batch_size, num_channels, num_samples = waveform.shape

        # 计算音频时长（秒）
        duration = num_samples / sample_rate

        # 获取音频的其他信息
        dtype = waveform.dtype
        device = waveform.device

        # 计算音频的一些统计信息
        min_value = waveform.min().item()
        max_value = waveform.max().item()
        mean_value = waveform.mean().item()
        std_value = waveform.std().item()

        # 构建音频信息文本，去掉标题和底部分隔线
        audio_info_text = f"采样率 (Sample Rate): {sample_rate} Hz\n"
        audio_info_text += f"时长 (Duration): {duration:.2f} 秒\n"
        audio_info_text += f"通道数 (Channels): {num_channels}\n"
        audio_info_text += f"样本数 (Samples): {num_samples}\n"
        audio_info_text += f"数据类型 (Data Type): {dtype}\n"
        audio_info_text += f"设备 (Device): {device}\n"
        audio_info_text += f"最小值 (Min Value): {min_value:.6f}\n"
        audio_info_text += f"最大值 (Max Value): {max_value:.6f}\n"
        audio_info_text += f"平均值 (Mean Value): {mean_value:.6f}\n"
        audio_info_text += f"标准差 (Std Value): {std_value:.6f}\n"
        audio_info_text += f"批次大小 (Batch Size): {batch_size}"

        # 直接打印音频信息到控制台，这样用户可以在日志中看到
        print(audio_info_text)

        # 返回UI输出和结果，模仿ComfyUI-Easy-Use节点的实现方式
        return {
            "ui": {
                "text": audio_info_text
            },
            "result": (audio_info_text,)
        }


# 节点类映射，用于ComfyUI系统识别
NODE_CLASS_MAPPINGS = {
    "OLO_AudioInfo": OLO_AudioInfo
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_AudioInfo": "OLO Audio Info"
}
