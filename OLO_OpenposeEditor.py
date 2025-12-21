import json
import os
import torch
import numpy as np
import cv2
import math
import folder_paths
from PIL import Image
from .util import draw_pose_json, draw_pose, extend_scalelist, pose_normalized
from nodes import LoadImage

OpenposeJSON = dict


class OLO_OpenposeEditor:
    """
    OLO OpenPose Editor节点实现
    这是一个增强版的OpenPose编辑器，结合了原始OpenPose-Editor-Plus的编辑功能和OLO的渲染功能
    """
    NODE_NAME = "OLO_OpenposeEditor"
    NODE_CATEGORY = "OLO/pose"

    # 添加OUTPUT_NODE标记，使节点显示open editor按钮
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("STRING", {"default": ""}),
            },
            "optional": {
                "show_body": ("BOOLEAN", {"default": True}),
                "show_face": ("BOOLEAN", {"default": True}),
                "show_hands": ("BOOLEAN", {"default": True}),
                "resolution_x": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 12800,
                    "tooltip": "Resolution X. -1 means use the original resolution."
                }),
                "pose_marker_size": ("INT", {
                    "default": 4,
                    "min": 0,
                    "max": 100
                }),
                "face_marker_size": ("INT", {
                    "default": 3,
                    "min": 0,
                    "max": 100
                }),
                "hand_marker_size": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 100
                }),
                "hands_scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.05
                }),
                "body_scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.05
                }),
                "head_scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.05
                }),
                "overall_scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.05
                }),
                "scalelist_behavior": (["poses", "images"], {"default": "poses", "tooltip": "When the scale input is a list, this determines how the scale list takes effect, the differences appear when there are multiple persons(poses) in one image."}),
                "match_scalelist_method": (["no extend", "loop extend", "clamp extend"], {"default": "loop extend", "tooltip": "Match the scale list to the input poses or images when the scale list length is shorter. No extend: Beyound the scale list will be 1.0. Loop: Loop the scale list to match the poses or images length. Clamp: Use the last scale value to extend the scale list."}),
                "only_scale_pose_index": ("INT", {
                    "default": 99,
                    "min": -100,
                    "max": 100,
                    "tooltip": "For multiple poses in one image, the scale will be only applied at desired index. If set to a number larger than the number of poses in the image, the scale will be applied to all poses. Negative number will apply to the pose from the end."
                }),
                "output_width_for_dwpose": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "output_height_for_dwpose": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "scale_for_xinsr_for_dwpose": ("BOOLEAN", {"default": False}),
                "canvas_width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "canvas_height": ("INT", {"default": 768, "min": 64, "max": 4096, "step": 64}),
                "pose_filter_index": ("INT", {"default": -1, "min": -1, "max": 100, "tooltip": "Filter poses by index. -1 means show all poses."}),
            },
            "hidden": {
                "savedPose": ("STRING", {"multiline": True}),
                "backgroundImage": ("STRING", {"multiline": False}),
                "POSE_JSON": ("STRING", {"multiline": True}),
                "POSE_KEYPOINT": ("POSE_KEYPOINT", {"default": None}),
                "poseFilterIndex": ("INT", {"default": -1}),
            }
        }

    RETURN_NAMES = ("POSE_IMAGE", "POSE_KEYPOINT", "POSE_JSON", "pose_image",
                    "combined_image", "dw_pose_image", "dw_combined_image")
    RETURN_TYPES = ("IMAGE", "POSE_KEYPOINT", "STRING",
                    "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    OUTPUT_NODE = True
    FUNCTION = "load_pose"
    CATEGORY = "OLO/pose"

    # 类变量，用于存储上次的指纹，确保IS_CHANGED函数稳定运行
    _last_fingerprints = {}

    @classmethod
    def IS_CHANGED(cls, image, savedPose, backgroundImage, POSE_JSON, POSE_KEYPOINT,
                   show_body, show_face, show_hands, resolution_x, pose_marker_size,
                   face_marker_size, hand_marker_size, hands_scale, body_scale, head_scale,
                   overall_scale, scalelist_behavior, match_scalelist_method, only_scale_pose_index,
                   output_width_for_dwpose, output_height_for_dwpose, scale_for_xinsr_for_dwpose,
                   canvas_width, canvas_height, pose_filter_index, **kwargs):
        """计算节点状态变化的指纹"""
        fingerprint = f"{savedPose}-{backgroundImage}-{POSE_JSON}-{output_width_for_dwpose}-{output_height_for_dwpose}-{scale_for_xinsr_for_dwpose}-{canvas_width}-{canvas_height}-{pose_filter_index}"
        return fingerprint

    def render_dw_pose(self, pose_json, width, height, scale_for_xinsr):
        """
        渲染DW风格的姿态图像

        Args:
            pose_json: 姿态JSON数据
            width: 输出图像宽度
            height: 输出图像高度
            scale_for_xinsr: 是否为XinSR模型调整线条宽度

        Returns:
            RGB格式的NumPy数组
        """
        if not pose_json or not pose_json.strip():
            return np.zeros((height, width, 3), dtype=np.uint8)
        try:
            data = json.loads(pose_json)
        except json.JSONDecodeError:
            return np.zeros((height, width, 3), dtype=np.uint8)

        target_w, target_h = width, height
        original_w, original_h = data.get(
            'width', target_w), data.get('height', target_h)
        scale_x, scale_y = target_w / original_w, target_h / original_h

        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        people = data.get('people', [])
        if not people:
            return canvas

        limbSeq = [[2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8], [2, 9], [9, 10], [
            10, 11], [2, 12], [12, 13], [13, 14], [2, 1], [1, 15], [15, 17], [1, 16], [16, 18]]
        colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0], [0, 255, 85], [0, 255, 170], [
            0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]

        BASE_RESOLUTION_SIDE = 512.0
        base_thickness = 2.0
        target_max_side = max(target_w, target_h)
        scale_factor = target_max_side / BASE_RESOLUTION_SIDE
        scaled_joint_radius = int(max(1, base_thickness * scale_factor))
        scaled_stickwidth = scaled_joint_radius

        if scale_for_xinsr:
            xinsr_stick_scale = 1 if target_max_side < 500 else min(
                2 + (target_max_side // 1000), 7)
            scaled_stickwidth *= xinsr_stick_scale

        for person in people:
            keypoints_flat = person.get('pose_keypoints_2d', [])
            keypoints = [(int(keypoints_flat[i] * scale_x), int(keypoints_flat[i+1] * scale_y))
                         if keypoints_flat[i+2] > 0 else None for i in range(0, len(keypoints_flat), 3)]

            for limb_indices, color in zip(limbSeq, colors):
                k1_idx, k2_idx = limb_indices[0] - 1, limb_indices[1] - 1
                if k1_idx >= len(keypoints) or k2_idx >= len(keypoints):
                    continue
                p1, p2 = keypoints[k1_idx], keypoints[k2_idx]
                if p1 is None or p2 is None:
                    continue

                Y, X = np.array([p1[0], p2[0]]), np.array([p1[1], p2[1]])
                mX, mY = np.mean(X), np.mean(Y)
                length = np.sqrt((X[0] - X[1])**2 + (Y[0] - Y[1])**2)
                angle = math.degrees(math.atan2(X[0] - X[1], Y[0] - Y[1]))

                polygon = cv2.ellipse2Poly((int(mY), int(mX)), (int(
                    length / 2), scaled_stickwidth), int(angle), 0, 360, 1)
                cv2.fillConvexPoly(canvas, polygon, [
                                   int(c * 0.6) for c in color])

            for i, keypoint in enumerate(keypoints):
                if keypoint is None:
                    continue
                if i >= len(colors):
                    continue
                cv2.circle(canvas, keypoint, scaled_joint_radius,
                           colors[i], thickness=-1)

        return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)  # 返回RGB格式的NumPy数组

    def load_pose(self, image="", savedPose="", backgroundImage="", POSE_JSON="", POSE_KEYPOINT=None,
                  show_body=True, show_face=True, show_hands=True, resolution_x=-1, pose_marker_size=4,
                  face_marker_size=3, hand_marker_size=2, hands_scale=1.0, body_scale=1.0, head_scale=1.0,
                  overall_scale=1.0, scalelist_behavior="poses", match_scalelist_method="loop extend",
                  only_scale_pose_index=99, output_width_for_dwpose=512, output_height_for_dwpose=512,
                  scale_for_xinsr_for_dwpose=False, canvas_width=512, canvas_height=768, pose_filter_index=-1):
        '''
        加载姿势数据并生成姿势图像，支持多种输出格式

        Args:
            image: 输入图像路径
            savedPose: 从编辑器保存的姿态数据
            backgroundImage: 背景图像路径
            POSE_JSON: 姿势JSON数据
            POSE_KEYPOINT: 姿态关键点数据
            show_body: 是否显示身体关键点
            show_face: 是否显示面部关键点
            show_hands: 是否显示手部关键点
            resolution_x: 输出图像宽度，-1表示使用原始分辨率
            pose_marker_size: 身体标记点大小
            face_marker_size: 面部标记点大小
            hand_marker_size: 手部标记点大小
            hands_scale: 手部缩放比例
            body_scale: 身体缩放比例
            head_scale: 头部缩放比例
            overall_scale: 整体缩放比例
            scalelist_behavior: 缩放列表行为
            match_scalelist_method: 匹配缩放列表方法
            only_scale_pose_index: 仅缩放指定索引的姿势
            output_width_for_dwpose: DW姿态输出宽度
            output_height_for_dwpose: DW姿态输出高度
            scale_for_xinsr_for_dwpose: 是否为XinSR模型调整线条宽度
            canvas_width: 画布宽度
            canvas_height: 画布高度
            pose_filter_index: 姿态过滤器索引

        Returns:
            tuple: 包含多种输出的元组
                - POSE_IMAGE: OLO风格的姿态图像
                - POSE_KEYPOINT: 姿态关键点数据
                - POSE_JSON: 姿态JSON字符串
                - pose_image: 原始Fabric.js风格的姿态图像
                - combined_image: 合成图像
                - dw_pose_image: DW风格的纯姿态图像
                - dw_combined_image: DW风格的合成图像
        '''
        # 初始化所有输出
        pose_imgs_np = None
        pose_data = None
        pose_json_str = ""
        pose_image_fabric = None
        combined_image_fabric = None
        dw_pose_image = None
        dw_combined_image = None

        # 处理姿态数据 - 优先使用savedPose，然后是POSE_JSON，最后是POSE_KEYPOINT
        pose_source = None
        if savedPose and savedPose.strip():
            pose_source = savedPose
            pose_json_str = savedPose
        elif POSE_JSON and POSE_JSON.strip():
            pose_source = POSE_JSON
            pose_json_str = POSE_JSON
        elif POSE_KEYPOINT is not None:
            pose_source = json.dumps(POSE_KEYPOINT, indent=4)
            pose_json_str = pose_source

        # 如果有姿态数据，生成OLO风格的姿态图像
        if pose_source:
            try:
                # 标准化JSON格式
                pose_source = pose_source.replace(
                    "'", '"').replace('None', '[]')

                # 解析JSON并生成OLO风格的姿势图像
                hands_scalelist, body_scalelist, head_scalelist, overall_scalelist = extend_scalelist(
                    scalelist_behavior, pose_source, hands_scale, body_scale, head_scale, overall_scale,
                    match_scalelist_method, only_scale_pose_index)
                normalized_pose_json = pose_normalized(pose_source)
                pose_imgs, POSE_PASS_SCALED = draw_pose_json(normalized_pose_json, resolution_x, show_body, show_face, show_hands,
                                                             pose_marker_size, face_marker_size, hand_marker_size, hands_scalelist, body_scalelist, head_scalelist, overall_scalelist)

                if pose_imgs:
                    pose_imgs_np = np.array(pose_imgs).astype(np.float32) / 255
                    pose_data = POSE_PASS_SCALED
                    pose_json_str = json.dumps(POSE_PASS_SCALED, indent=4)
            except Exception as e:
                print(f"Error processing pose data: {e}")

        # 如果没有生成OLO风格的姿态图像，创建空白图像
        if pose_imgs_np is None:
            W = 512
            H = 768
            pose_draw = dict(
                bodies={'candidate': [], 'subset': []}, faces=[], hands=[])
            pose_out = dict(pose_keypoints_2d=[], face_keypoints_2d=[],
                            hand_left_keypoints_2d=[], hand_right_keypoints_2d=[])
            pose_data = {"people": [pose_out],
                         "canvas_height": H, "canvas_width": W}

            W_scaled = resolution_x
            if resolution_x < 64:
                W_scaled = W
            H_scaled = int(H*(W_scaled*1.0/W))
            pose_img = [draw_pose(pose_draw, H_scaled, W_scaled,
                                  pose_marker_size, face_marker_size, hand_marker_size)]
            pose_imgs_np = np.array(pose_img).astype(np.float32) / 255
            pose_json_str = json.dumps(pose_data)

        # 处理原始Fabric.js风格的图像
        if image and image.strip():
            # 使用LoadImage节点加载图像
            load_image = LoadImage()
            pose_image_fabric, _ = load_image.load_image(image)

            base_name, ext = os.path.splitext(image)
            combined_image_name = f"{base_name}_combined{ext}"
            combined_image_path = folder_paths.get_annotated_filepath(
                combined_image_name)

            if not os.path.exists(combined_image_path):
                combined_image_fabric = pose_image_fabric
            else:
                combined_image_fabric, _ = load_image.load_image(
                    combined_image_name)
        else:
            # 如果image为空，创建一个默认的空白图像
            W = 512
            H = 768
            blank_image_np = np.ones((H, W, 3), dtype=np.float32) * 0.5
            pose_image_fabric = torch.from_numpy(blank_image_np).unsqueeze(0)
            combined_image_fabric = pose_image_fabric

        # 生成DW风格的姿态图像
        dw_pose_np = self.render_dw_pose(
            pose_json_str, output_width_for_dwpose, output_height_for_dwpose, scale_for_xinsr_for_dwpose)
        dw_pose_image = torch.from_numpy(
            dw_pose_np.astype(np.float32) / 255.0).unsqueeze(0)

        # 生成DW风格的合成图像
        if backgroundImage and backgroundImage.strip() != "":
            # 1. 加载背景图
            bg_image_path = folder_paths.get_annotated_filepath(
                backgroundImage)
            if os.path.exists(bg_image_path):
                bg_image_pil = Image.open(bg_image_path)
                bg_image_np = np.array(bg_image_pil.convert("RGB"))

                # 2. 缩放背景图到目标尺寸
                bg_image_resized = cv2.resize(
                    bg_image_np, (output_width_for_dwpose, output_height_for_dwpose), interpolation=cv2.INTER_AREA)

                # 3. 创建蒙版并进行合成
                dw_pose_gray = cv2.cvtColor(dw_pose_np, cv2.COLOR_RGB2GRAY)
                _, mask = cv2.threshold(
                    dw_pose_gray, 1, 255, cv2.THRESH_BINARY)

                # 4. 使用蒙版将骨骼"粘贴"到背景上
                dw_combined_np = bg_image_resized.copy()
                dw_combined_np[mask != 0] = dw_pose_np[mask != 0]

                dw_combined_image = torch.from_numpy(
                    dw_combined_np.astype(np.float32) / 255.0).unsqueeze(0)
            else:
                # 如果背景文件找不到，就返回纯姿态图
                dw_combined_image = dw_pose_image
        else:
            # 如果没有背景，则合成图就是纯姿态图
            dw_combined_image = dw_pose_image

        # 返回所有结果
        return {
            "ui": {
                "savedPose": [savedPose],
                "backgroundImage": [backgroundImage],
                "canvas_width": [canvas_width],
                "canvas_height": [canvas_height],
                "pose_filter_index": [pose_filter_index]
            },
            "result": (torch.from_numpy(pose_imgs_np), pose_data, pose_json_str, pose_image_fabric, combined_image_fabric, dw_pose_image, dw_combined_image)
        }


class OLO_OriginalOpenPoseEditor:
    # 原始OpenPose Editor节点实现
    NODE_NAME = "OLO_OriginalOpenPoseEditor"
    NODE_CATEGORY = "OLO/pose"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "image": ("STRING", {"default": ""}),
            },
            "hidden": {
                "savedPose": ("STRING", {"multiline": True}),
                "backgroundImage": ("STRING", {"multiline": False}),
            }
        }

    # 添加OUTPUT_NODE标记，使节点显示open editor按钮
    OUTPUT_NODE = True
    RETURN_TYPES = ("IMAGE", "IMAGE", "POSE_KEYPOINT", "STRING",)
    RETURN_NAMES = ("pose_image", "combined_image",
                    "POSE_KEYPOINT", "POSE_JSON",)
    FUNCTION = "get_images"
    CATEGORY = "OLO/pose"

    @classmethod
    def IS_CHANGED(cls, image, savedPose, backgroundImage, **kwargs):
        # 高效地计算并返回指纹
        fingerprint = f"{savedPose}-{backgroundImage}"
        return fingerprint

    def get_images(self, image, savedPose="", backgroundImage=""):
        # 初始化返回的图像
        pose_image_fabric = None
        combined_image_fabric = None

        # 解析savedPose为POSE_KEYPOINT格式
        pose_data = {
            "people": [{"pose_keypoints_2d": [], "face_keypoints_2d": [], "hand_left_keypoints_2d": [], "hand_right_keypoints_2d": []}],
            "canvas_height": 768,
            "canvas_width": 512
        }

        # 优先使用savedPose（从编辑器保存的姿势）
        if savedPose and savedPose.strip():
            try:
                pose_data = json.loads(savedPose)
            except json.JSONDecodeError:
                pose_data = pose_data

        pose_json_str = json.dumps(pose_data)

        # 只有当image不为空时才加载图像
        if image and image.strip():
            # 使用正确的方式调用LoadImage节点
            load_image = LoadImage()
            pose_image_fabric, _ = load_image.load_image(image)

            base_name, ext = os.path.splitext(image)
            combined_image_name = f"{base_name}_combined{ext}"
            combined_image_path = folder_paths.get_annotated_filepath(
                combined_image_name)

            if not os.path.exists(combined_image_path):
                combined_image_fabric = pose_image_fabric
            else:
                combined_image_fabric, _ = load_image.load_image(
                    combined_image_name)
        else:
            # 如果image为空，创建一个默认的空白图像
            W = 512
            H = 768
            blank_image_np = np.ones((H, W, 3), dtype=np.float32) * 0.5
            pose_image_fabric = torch.from_numpy(blank_image_np).unsqueeze(0)
            combined_image_fabric = pose_image_fabric

        # 返回结果，支持UI输出
        return {
            "ui": {
                "savedPose": [savedPose],
                "backgroundImage": [backgroundImage]
            },
            "result": (pose_image_fabric, combined_image_fabric, pose_data, pose_json_str,)
        }
