import torch
from comfy.utils import logging

logger = logging.getLogger(__name__)


class OLO_WanFrame:
    CATEGORY = "OLO/Frame"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("Result",)

    INPUT_IS_LIST = False

    @classmethod
    def INPUT_TYPES(cls): return {
        "required": {
            "use_custom_frame_count": ("BOOLEAN", {"default": False, "label_on": "Enable", "label_off": "Disable"}),
            "input_video_frame_unit": ("INT", {"default": 4, "min": 0, "max": 9999, "step": 1}),
            "frame_multiplier": ("INT", {"default": 13, "min": 1, "max": 999, "step": 1}),
            "frame_addition_value": ("INT", {"default": 1, "min": 0, "max": 9999, "step": 1}),

            "custom_input_frame_count": ("INT", {"default": 0, "min": 0, "max": 9999, "step": 1}),
        }
    }

    FUNCTION = "calculate"
    DISPLAY_NAME = "OLO Frame Calculation"

    def calculate(self, use_custom_frame_count, input_video_frame_unit, frame_multiplier, frame_addition_value, custom_input_frame_count):
        try:
            if use_custom_frame_count:
                result = custom_input_frame_count
                logger.info(f"Using custom frame count: {result}")
            else:
                result = input_video_frame_unit * frame_multiplier + frame_addition_value
                logger.info(
                    f"Frame calculation completed: {input_video_frame_unit} × {frame_multiplier} + {frame_addition_value} = {result}")
            return (result,)
        except Exception as e:
            logger.error(f"Frame calculation error: {str(e)}")
            return (0,)


NODE_CLASS_MAPPINGS = {
    "OLO_WanFrame": OLO_WanFrame
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_WanFrame": "OLO Frame Calculation"
}
