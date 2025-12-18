MY_CATEGORY = "OLO/Audio"

try:
    import torch
except ImportError:
    # 确保在 ComfyUI 环境中 torch 可用
    raise ImportError(
        "PyTorch (torch) is required for audio processing nodes but was not found.")


class OLO_AudioConcat(object):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "inputcount": ("INT", {"default": 2, "min": 2, "max": 1000, "step": 1}),
                "start_spacer": ("FLOAT",
                                 {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.1, "label": "Start Silence (s)"}),
                # 新增：中间间隔 (middle)
                "middle_spacer": ("FLOAT",
                                  {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.1, "label": "Between Silence (s)"}),
                # 新增：结束间隔 (end)
                "end_spacer": ("FLOAT",
                               {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.1, "label": "End Silence (s)"}),
            },
            "optional": {
                "audio_1": ("AUDIO", {"force_output": True}),
                "mute_1": ("BOOLEAN", {"default": False, "label": "Mute Audio 1"}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("concatenated_audio",)
    FUNCTION = "execute"
    CATEGORY = MY_CATEGORY

    def _create_silence_tensor(self, duration, sample_rate, reference_tensor):
        """根据时长和参考张量创建静音张量"""
        if duration <= 0.0:
            return None

        num_silent_samples = int(duration * sample_rate)

        # 保持 Batch 和 Channel 维度不变，时间维度设为静音长度
        silent_shape = list(reference_tensor.shape)
        silent_shape[-1] = num_silent_samples

        # 创建全零静音张量，保持 dtype 和 device 一致
        silence_tensor = torch.zeros(tuple(silent_shape),
                                     dtype=reference_tensor.dtype,
                                     device=reference_tensor.device)
        return silence_tensor

    def execute(self, inputcount, audio_1, mute_1=False, start_spacer=0.0, middle_spacer=0.0, end_spacer=0.0, **kwargs):
        """
        执行音频拼接操作，支持动态数量的音频输入

        参数:
            inputcount: 输入音频的数量
            audio_1: 第一个音频对象（必填）
            mute_1: 是否静音第一个音频
            start_spacer: 开始静音间隔时长
            middle_spacer: 音频之间的静音间隔时长
            end_spacer: 结束静音间隔时长
            **kwargs: 动态参数，包含audio_2到audio_N和对应的mute_2到mute_N

        返回:
            拼接后的音频对象
        """
        # 1. 提取第一个音频的采样率作为基准
        sample_rate = audio_1["sample_rate"]
        reference_waveform = audio_1["waveform"]

        # 2. 初始化音频列表和静音列表
        audio_list = [audio_1]
        mute_list = [mute_1]

        # 添加其他音频（从audio_2到audio_N）
        for i in range(2, inputcount + 1):
            audio_key = f"audio_{i}"
            mute_key = f"mute_{i}"

            # 获取音频和静音参数，如果不存在则使用默认值
            audio_item = kwargs.get(audio_key)
            mute_item = kwargs.get(mute_key, False)

            if audio_item is not None:
                audio_list.append(audio_item)
                mute_list.append(mute_item)

        # 3. 初始化拼接列表
        parts_to_concat = []

        # a. 开始间隔
        start_silence = self._create_silence_tensor(
            start_spacer, sample_rate, reference_waveform)
        if start_silence is not None:
            parts_to_concat.append(start_silence)

        # 4. 处理所有音频
        for i, audio_item in enumerate(audio_list):
            # 验证采样率
            if sample_rate != audio_item["sample_rate"]:
                raise ValueError(
                    f"Audio sample rate mismatch: audio {i+1} has {audio_item['sample_rate']} Hz, but expected {sample_rate} Hz.")

            waveform = audio_item["waveform"]

            # 检查是否需要静音当前音频
            current_mute = mute_list[i]

            # 如果需要静音，则将波形替换为静音
            if current_mute:
                duration = waveform.shape[-1] / sample_rate
                waveform = self._create_silence_tensor(
                    duration, sample_rate, waveform)

            # 添加当前音频
            if waveform is not None:
                parts_to_concat.append(waveform)

            # 添加音频之间的间隔（除了最后一个音频）
            if i < len(audio_list) - 1:
                middle_silence = self._create_silence_tensor(
                    middle_spacer, sample_rate, reference_waveform)
                if middle_silence is not None:
                    parts_to_concat.append(middle_silence)

        # e. 结束间隔
        end_silence = self._create_silence_tensor(
            end_spacer, sample_rate, reference_waveform)
        if end_silence is not None:
            parts_to_concat.append(end_silence)

        # 6. 执行拼接
        if not parts_to_concat:
            # 如果所有输入都无效，则返回一个空的音频
            return ({"waveform": torch.empty(1, 2, 0), "sample_rate": sample_rate},)

        # 沿着最后一个维度（时间维度）拼接所有部分
        final_waveform = torch.cat(parts_to_concat, dim=-1)

        # 7. 返回新的 AUDIO 结构
        result_audio = {
            "waveform": final_waveform,
            "sample_rate": sample_rate
        }

        return (result_audio,)


# 节点类映射，用于ComfyUI系统识别
NODE_CLASS_MAPPINGS = {
    "OLO_AudioConcat": OLO_AudioConcat
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_AudioConcat": "OLO Audio Concat"
}
