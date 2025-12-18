import torch
from comfy.utils import logging


logger = logging.getLogger(__name__)


class OLO_FrameHold:
    CATEGORY = "OLO/Frame"

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output",)

    INPUT_IS_LIST = False

    @classmethod
    def INPUT_TYPES(cls): return {
        "required": {
            "image": ("IMAGE",),
            "frame_index": ("INT", {
                "default": 1,
                "min": 1,
                "max": 9999,
                "step": 1
            }),
        }
    }

    FUNCTION = "extract_frame"
    DISPLAY_NAME = "OLO Frame Extract"

    def extract_frame(self, image, frame_index):

        try:
            frame_count = image.shape[0]
            zero_based_index = frame_index - 1

            if zero_based_index < 0 or zero_based_index >= frame_count:
                error_msg = f"Frame index out of range! Valid range: 1-{frame_count}, Input: {frame_index}"
                logger.error(error_msg)

                return (image[0:1, ...],)

            selected_frame = image[zero_based_index:zero_based_index+1, ...]
            logger.info(
                f"Successfully extracted frame {frame_index} (0-based: {zero_based_index})")
            return (selected_frame,)

        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
            return (torch.zeros(1, 1, 1, 3, dtype=torch.float32),)


NODE_CLASS_MAPPINGS = {
    "OLO_FrameHold": OLO_FrameHold
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_FrameHold": "OLO Frame Extract"
}
