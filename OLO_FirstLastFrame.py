import torch
from comfy.utils import logging

# 配置日志模块，用于记录节点的运行信息
logger = logging.getLogger(__name__)


class OLO_FirstLastFrame:
    """
    视频首尾帧提取节点

    该节点用于从视频帧序列中同时提取第一帧和最后一帧，
    并支持自定义文件名生成和错误处理。
    """

    # 定义节点的分类
    CATEGORY = "OLO/Frame"

    # 定义节点的输出类型
    # "IMAGE" 表示输出是图像张量，"STRING" 表示输出是文件名
    RETURN_TYPES = ("IMAGE", "IMAGE", "STRING", "STRING")
    # 定义输出的显示名称
    RETURN_NAMES = ("first_frame", "last_frame",
                    "first_frame_name", "last_frame_name")

    # 指示输入是否为列表类型
    INPUT_IS_LIST = False
    # 指示输出是否为列表类型
    OUTPUT_IS_LIST = False

    # 定义节点的输入参数
    @classmethod
    def INPUT_TYPES(cls): return {
        "required": {
            "image": ("IMAGE",),  # 输入图像张量序列
            "return_first_on_error": ("BOOLEAN", {"default": True, "label_on": "yes", "label_off": "no"}),
        },
        "optional": {
            # 视频名称，用于自定义输出文件名
            "video_name": ("STRING", {"default": "video_", "multiline": False}),
        }
    }

    # 定义节点的主要功能函数名称
    FUNCTION = "extract_first_last_frames"

    # 节点在UI中的显示名称
    DISPLAY_NAME = "OLO 提取首尾帧"

    def extract_first_last_frames(self, image, return_first_on_error=True, video_name="video_"):
        """
        从图像张量序列中同时提取第一帧和最后一帧，并生成自定义文件名

        参数:
            image: torch.Tensor - 输入图像张量序列，形状为 [帧数量, 高度, 宽度, 通道数]
            return_first_on_error: bool - 当出错时是否返回第一帧作为备选
            video_name: str - 视频名称，用于自定义输出文件名

        返回:
            tuple: 包含提取的第一帧、最后一帧以及它们的文件名的元组
                   (first_frame_tensor, last_frame_tensor, first_frame_name_string, last_frame_name_string)

        异常:
            Exception: 当提取失败时记录错误信息
        """
        try:
            # 检查输入是否为torch.Tensor类型
            if not isinstance(image, torch.Tensor):
                logger.error("Input is not a valid torch.Tensor")
                # 返回默认的1x1黑色帧和错误文件名
                default_frame = torch.zeros(1, 1, 1, 3, dtype=torch.float32)
                error_filename = f"{video_name}_错误帧"
                return (default_frame, default_frame, error_filename, error_filename)

            # 获取帧数量
            frame_count = image.shape[0]
            logger.info(f"输入帧数量: {frame_count}")

            # 确保至少有一帧
            if frame_count > 0:
                # 提取第一帧
                first_frame = image[0:1, ...]  # 使用切片保持维度
                # 提取最后一帧 (Python中-1表示最后一个元素)
                last_frame = image[-1:, ...]  # 使用切片保持维度

                # 生成自定义文件名
                first_frame_name = f"{video_name}_first_frame1_"
                last_frame_name = f"{video_name}_last_frame{frame_count}_"

                logger.info(f"成功提取首帧和尾帧，总帧数: {frame_count}")
                return (first_frame, last_frame, first_frame_name, last_frame_name)
            else:
                # 如果没有帧，记录错误并根据选项返回结果
                logger.error("No frames available in the input tensor")

                if return_first_on_error:
                    # 如果选项为True，返回1x1的黑色帧
                    logger.warning(
                        "No frames available, returning 1x1 black frames")
                    default_frame = torch.zeros(
                        1, 1, 1, 3, dtype=torch.float32)
                    error_filename = f"{video_name}_error_frame"
                    return (default_frame, default_frame, error_filename, error_filename)
                else:
                    # 如果选项为False，返回空帧
                    logger.warning("Returning empty frames as per settings")
                    empty_frame = torch.zeros(0, 0, 0, 3, dtype=torch.float32)
                    empty_filename = f"{video_name}_empty_frame"
                    return (empty_frame, empty_frame, empty_filename, empty_filename)

        except Exception as e:
            # 捕获所有异常并记录错误信息
            logger.error(f"Error extracting frames: {str(e)}")

            try:
                # 尝试获取第一帧作为备选
                if return_first_on_error and image.shape[0] > 0:
                    first_frame = image[0:1, ...]
                    logger.info("Returned first frame as fallback on error")
                    # 使用第一帧作为首帧和尾帧的备选
                    error_filename = f"{video_name}_error_using_first_frame"
                    return (first_frame, first_frame, error_filename, error_filename)
                else:
                    # 如果没有可用帧或不返回第一帧，创建一个1x1的黑色帧
                    logger.warning(
                        "Error occurred and no frames available, returning 1x1 black frames")
                    default_frame = torch.zeros(
                        1, 1, 1, 3, dtype=torch.float32)
                    error_filename = f"{video_name}_error_using_black_frame"
                    return (default_frame, default_frame, error_filename, error_filename)
            except:
                # 最安全的备选选项
                default_frame = torch.zeros(1, 1, 1, 3, dtype=torch.float32)
                error_filename = f"{video_name}_error_default_black_frame"
                return (default_frame, default_frame, error_filename, error_filename)


# 节点类映射，用于ComfyUI系统识别
NODE_CLASS_MAPPINGS = {
    "OLO_FirstLastFrame": OLO_FirstLastFrame
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_FirstLastFrame": "OLO 提取首尾帧"
}
