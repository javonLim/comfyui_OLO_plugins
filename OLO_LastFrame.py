import torch
from comfy.utils import logging

# 创建日志记录器，用于记录节点执行过程中的信息和错误
logger = logging.getLogger(__name__)


class OLO_LastFrame:
    """
    提取视频序列最后一帧的节点

    该节点接收一个视频帧序列，并自动提取其中的最后一帧。
    适用于需要获取视频结尾帧进行进一步处理的场景。
    """
    # 节点在ComfyUI中的分类
    CATEGORY = "OLO/Frame"

    # 定义节点的输出类型
    # "IMAGE" 表示输出是一个图像张量，"STRING" 表示输出是一个文件名
    RETURN_TYPES = ("IMAGE", "STRING")
    # 定义输出的显示名称
    RETURN_NAMES = ("last_frame", "filename")

    # 指示输入是否为列表类型
    INPUT_IS_LIST = False

    # 定义节点的输入参数
    @classmethod
    def INPUT_TYPES(cls): return {
        "required": {
            "image": ("IMAGE",),  # 输入视频帧序列
            "return_first_on_error": ("BOOLEAN", {"default": True, "label_on": "yes", "label_off": "no"}),
        },
        "optional": {
            # 尾帧图像名称，用于自定义输出文件名
            # 注意：PyTorch张量本身不包含名称信息，需要手动提供或从其他节点连接
            "last_frame_name": ("STRING", {"default": "last_frame_", "multiline": False}),
        }
    }

    # 指定要调用的函数名称
    FUNCTION = "extract_last_frame"

    # 节点在UI中的显示名称
    DISPLAY_NAME = "OLO 提取最后一帧"

    def extract_last_frame(self, image, return_first_on_error=True, last_frame_name="last_frame_"):
        """
        从视频帧序列中提取最后一帧，并生成自定义文件名

        参数:
            image: torch.Tensor - 输入视频帧序列，形状为 [帧数量, 高度, 宽度, 通道数]
            return_first_on_error: bool - 当出错时是否返回第一帧作为备选
            last_frame_name: str - 尾帧图像名称，用于自定义输出文件名
                                注意：image输入张量不包含名称信息，需要手动提供或从其他节点连接
                                如果未提供，将使用默认值"last_frame_"

        返回:
            tuple: 包含提取的最后一帧和生成的文件名的元组
                   (image_tensor, filename_string)

        异常:
            Exception: 当提取失败时记录错误信息
        """
        # 注意：PyTorch张量(image)本身不包含名称元数据，因此无法直接从中提取图像名称
        # 需要通过last_frame_name参数手动提供名称，或从其他节点连接获取
        try:
            # 获取视频序列中的帧数量
            frame_count = image.shape[0]

            # 确保至少有一帧
            if frame_count > 0:
                # 提取最后一帧 (Python中-1表示最后一个元素)
                # 使用切片保持维度，输出形状为 [1, 高度, 宽度, 通道数]
                last_frame = image[-1:, ...]
                # Generate custom filename: "video_name_frame{last_frame_index}_"
                # The last frame index is equal to the total frame count
                last_frame_index = frame_count
                custom_filename = f"{last_frame_name}_frame{last_frame_index}_"
                logger.info(
                    f"成功提取最后一帧，总帧数: {frame_count}，生成文件名: {custom_filename}")
                return (last_frame, custom_filename)
            else:
                # 如果没有帧，记录错误并根据选项返回结果
                error_msg = "输入视频序列为空，没有可提取的帧！"
                logger.error(error_msg)
                if return_first_on_error:
                    # If option is True but no frames available, create a 1x1 black frame as fallback
                    logger.warning(
                        "No frames available, returning a 1x1 black frame")
                    return (torch.zeros(1, 1, 1, 3, dtype=torch.float32), f"{last_frame_name}_error")
                else:
                    # If option is False, return empty frame
                    logger.warning("Returning empty frame as per settings")
                    return (torch.zeros(0, 0, 0, 3, dtype=torch.float32), f"{last_frame_name}_empty")

        except Exception as e:
            # 捕获所有可能的异常
            error_msg = f"提取最后一帧时出错: {str(e)}"
            logger.error(error_msg)

            # Error handling
            if return_first_on_error:
                try:
                    # 尝试返回第一帧作为备选
                    if image.shape[0] > 0:
                        first_frame = image[0:1, ...]
                        logger.info(
                            "Returned first frame as fallback on error")
                        return (first_frame, f"{last_frame_name}_error_using_first")
                    else:
                        # 如果没有可用帧，创建一个1x1的黑色帧
                        logger.warning(
                            "Error occurred and no frames available, returning a 1x1 black frame")
                        return (torch.zeros(1, 1, 1, 3, dtype=torch.float32), f"{last_frame_name}_error_using_black")
                except:
                    # 最安全的备选选项
                    return (torch.zeros(1, 1, 1, 3, dtype=torch.float32), f"{last_frame_name}_error_default_black")
            else:
                # 如果不返回第一帧，则返回空帧
                return (torch.zeros(0, 0, 0, 3, dtype=torch.float32), f"{last_frame_name}_empty")


# 定义节点类映射，用于ComfyUI识别和加载节点
NODE_CLASS_MAPPINGS = {
    "OLO_LastFrame": OLO_LastFrame
}

# 定义节点显示名称映射，用于在UI中显示友好的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_LastFrame": "OLO 提取最后一帧"
}
