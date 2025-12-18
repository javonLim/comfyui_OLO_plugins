MY_CATEGORY = "OLO/Test"


class OLO_TestTextOutput(object):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {"default": "Hello, World!"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "main"
    CATEGORY = MY_CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = "测试文本输出功能"

    def main(self, text_input):
        """
        测试文本输出功能

        参数:
            text_input: 输入文本

        返回:
            文本输出
        """
        return {"ui": {"text": (text_input,)}}


# 节点类映射，用于ComfyUI系统识别
NODE_CLASS_MAPPINGS = {
    "OLO_TestTextOutput": OLO_TestTextOutput
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "OLO_TestTextOutput": "OLO Test Text Output"
}
