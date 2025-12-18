import math
import numpy as np
import torch
import cv2
import matplotlib.colors

def _to_array_3(flat, n):
    """将扁平列表转换为3列数组

    Args:
        flat: 扁平列表
        n: 行数

    Returns:
        np.array: 转换后的数组
    """
    arr = np.array(flat, dtype=np.float32).reshape(n, 3)
    return arr

def _safe_array_3(flat, n):
    """安全地将扁平列表转换为3列数组，如果输入无效则返回零数组

    Args:
        flat: 扁平列表
        n: 行数

    Returns:
        np.array: 转换后的数组
    """
    if not isinstance(flat, (list, tuple)) or len(flat) < n * 3:
        return np.zeros((n, 3), dtype=np.float32)
    return _to_array_3(flat, n)

def _denorm_xy(arr, w, h):
    """将归一化的坐标反归一化到实际图像尺寸

    Args:
        arr: 包含坐标的数组
        w: 图像宽度
        h: 图像高度

    Returns:
        np.array: 反归一化后的数组
    """
    if arr[:, :2].max() <= 1.0:
        arr[:, 0] *= w
        arr[:, 1] *= h
    return arr

def _in_bounds(x, y, W, H):
    """检查坐标是否在图像边界内

    Args:
        x: x坐标
        y: y坐标
        W: 图像宽度
        H: 图像高度

    Returns:
        bool: 是否在边界内
    """
    return (x > 0.01) and (y > 0.01) and (0 <= x < W) and (0 <= y < H)

def draw_body17_keypoints_openpose_style(canvas, keypoints, scores=None, threshold=0.3, scale_for_xinsr=False):
    """使用OpenPose风格绘制17点身体关键点

    Args:
        canvas: 画布图像
        keypoints: 关键点坐标
        scores: 关键点置信度分数
        threshold: 置信度阈值
        scale_for_xinsr: 是否根据图像大小调整线条粗细

    Returns:
        np.array: 绘制后的图像
    """
    H, W, C = canvas.shape
    if keypoints is None or len(keypoints) < 18 or scores is None or len(scores) < 18:
        return canvas
    candidate = keypoints[:18].copy()
    candidate_scores = scores[:18].copy()
    avg_size = (H + W) / 2.0
    base_stickwidth = max(1, int(avg_size / 256))
    circle_radius = max(2, int(avg_size / 192))
    stickwidth = base_stickwidth
    if scale_for_xinsr:
        target_max_side = max(H, W)
        xinsr_stick_scale = 1 if target_max_side < 500 else min(2 + (target_max_side // 1000), 7)
        stickwidth = base_stickwidth * xinsr_stick_scale

    # 定义身体部位连接顺序
    limbSeq = [
        [2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8],
        [2, 9], [9, 10], [10, 11], [2, 12], [12, 13], [13, 14],
        [2, 1], [1, 15], [15, 17], [1, 16], [16, 18]
    ]

    # 定义颜色
    colors = [
        [255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0],
        [85, 255, 0], [0, 255, 0], [0, 255, 85], [0, 255, 170], [0, 255, 255],
        [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], [170, 0, 255],
        [255, 0, 255], [255, 0, 170], [255, 0, 85]
    ]

    # 绘制连接线
    for i, limb in enumerate(limbSeq):
        idx1, idx2 = limb[0] - 1, limb[1] - 1
        if idx1 < 0 or idx2 < 0 or idx1 >= 18 or idx2 >= 18: continue
        if candidate_scores[idx1] < threshold or candidate_scores[idx2] < threshold: continue
        Y, X = candidate[[idx1, idx2], 0], candidate[[idx1, idx2], 1]
        mX, mY = float(np.mean(X)), float(np.mean(Y))
        length = float(((X[0] - X[1]) ** 2 + (Y[0] - Y[1]) ** 2) ** 0.5)
        if length < 1.0: continue
        angle = math.degrees(math.atan2(X[0] - X[1], Y[0] - Y[1]))
        polygon = cv2.ellipse2Poly((int(mY), int(mX)), (int(length / 2), int(stickwidth)), int(angle), 0, 360, 1)
        cv2.fillConvexPoly(canvas, polygon, colors[i % len(colors)])

    # 绘制关键点
    for i in range(18):
        if candidate_scores[i] < threshold: continue
        x, y = int(candidate[i][0]), int(candidate[i][1])
        if 0 <= x < W and 0 <= y < H:
            cv2.circle(canvas, (x, y), circle_radius, colors[i % len(colors)], thickness=-1)

    return canvas

def draw_wholebody_keypoints_openpose_style(canvas, keypoints, scores=None, threshold=0.3, scale_for_xinsr=False):
    """使用OpenPose风格绘制全身关键点

    Args:
        canvas: 画布图像
        keypoints: 关键点坐标
        scores: 关键点置信度分数
        threshold: 置信度阈值
        scale_for_xinsr: 是否根据图像大小调整线条粗细

    Returns:
        np.array: 绘制后的图像
    """
    H, W, C = canvas.shape
    if keypoints is None or len(keypoints) < 134:
        return canvas

    max_hand_dist = math.sqrt(W**2 + H**2) / 5.0
    base_stickwidth = 4
    stickwidth = base_stickwidth
    if scale_for_xinsr:
        target_max_side = max(H, W)
        xinsr_stick_scale = 1 if target_max_side < 500 else min(2 + (target_max_side // 1000), 7)
        stickwidth = base_stickwidth * xinsr_stick_scale

    # 身体部位连接顺序
    body_limbSeq = [
        [2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8],
        [2, 9], [9, 10], [10, 11], [2, 12], [12, 13], [13, 14],
        [2, 1], [1, 15], [15, 17], [1, 16], [16, 18]
    ]

    # 手部连接顺序
    hand_edges = [
        [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8],
        [0, 9], [9, 10], [10, 11], [11, 12], [0, 13], [13, 14], [14, 15], [15, 16],
        [0, 17], [17, 18], [18, 19], [19, 20]
    ]

    # 定义颜色
    colors = [
        [255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0],
        [85, 255, 0], [0, 255, 0], [0, 255, 85], [0, 255, 170], [0, 255, 255],
        [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], [170, 0, 255],
        [255, 0, 255], [255, 0, 170], [255, 0, 85]
    ]

    # 绘制身体
    if len(keypoints) >= 18:
        for i, limb in enumerate(body_limbSeq):
            idx1, idx2 = limb[0] - 1, limb[1] - 1
            if idx1 < 0 or idx2 < 0 or idx1 >= 18 or idx2 >= 18: continue
            if scores is not None and (scores[idx1] < threshold or scores[idx2] < threshold): continue
            Y, X = np.array([keypoints[idx1][0], keypoints[idx2][0]], dtype=np.float32), np.array([keypoints[idx1][1], keypoints[idx2][1]], dtype=np.float32)
            mX, mY = float(np.mean(X)), float(np.mean(Y))
            length = float(((X[0] - X[1]) ** 2 + (Y[0] - Y[1]) ** 2) ** 0.5)
            if length < 1.0: continue
            angle = math.degrees(math.atan2(X[0] - X[1], Y[0] - Y[1]))
            polygon = cv2.ellipse2Poly((int(mY), int(mX)), (int(length / 2), int(stickwidth)), int(angle), 0, 360, 1)
            cv2.fillConvexPoly(canvas, polygon, colors[i % len(colors)])

        # 绘制身体关键点
        for i in range(18):
            if scores is not None and scores[i] < threshold: continue
            x, y = int(keypoints[i][0]), int(keypoints[i][1])
            if 0 <= x < W and 0 <= y < H:
                cv2.circle(canvas, (x, y), 4, colors[i % len(colors)], thickness=-1)

    # 绘制面部关键点
    if len(keypoints) >= 24:
        for i in range(18, 24):
            if scores is not None and scores[i] < threshold: continue
            x, y = int(keypoints[i][0]), int(keypoints[i][1])
            if 0 <= x < W and 0 <= y < H:
                cv2.circle(canvas, (x, y), 4, colors[i % len(colors)], thickness=-1)

    # 绘制脚关键点
    if len(keypoints) >= 92:
        for i in range(24, 92):
            if scores is not None and scores[i] < threshold: continue
            x, y = int(keypoints[i][0]), int(keypoints[i][1])
            if _in_bounds(x, y, W, H):
                cv2.circle(canvas, (x, y), 3, (255, 255, 255), thickness=-1)

    # 绘制左手
    if len(keypoints) >= 113:
        for ie, edge in enumerate(hand_edges):
            idx1, idx2 = 92 + edge[0], 92 + edge[1]
            if scores is not None and (scores[idx1] < threshold or scores[idx2] < threshold): continue
            x1, y1 = int(keypoints[idx1][0]), int(keypoints[idx1][1])
            x2, y2 = int(keypoints[idx2][0]), int(keypoints[idx2][1])
            line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if line_length > max_hand_dist:
                continue
            if _in_bounds(x1, y1, W, H) and _in_bounds(x2, y2, W, H):
                color = (matplotlib.colors.hsv_to_rgb([ie / float(len(hand_edges)), 1.0, 1.0]) * 255.0).astype(np.uint8)
                color = (int(color[0]), int(color[1]), int(color[2]))
                cv2.line(canvas, (x1, y1), (x2, y2), color, thickness=2)

        for i in range(92, 113):
            if scores is not None and scores[i] < threshold: continue
            x, y = int(keypoints[i][0]), int(keypoints[i][1])
            if _in_bounds(x, y, W, H):
                cv2.circle(canvas, (x, y), 4, (0, 0, 255), thickness=-1)

    # 绘制右手
    if len(keypoints) >= 134:
        for ie, edge in enumerate(hand_edges):
            idx1, idx2 = 113 + edge[0], 113 + edge[1]
            if scores is not None and (scores[idx1] < threshold or scores[idx2] < threshold): continue
            x1, y1 = int(keypoints[idx1][0]), int(keypoints[idx1][1])
            x2, y2 = int(keypoints[idx2][0]), int(keypoints[idx2][1])
            line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if line_length > max_hand_dist:
                continue
            if _in_bounds(x1, y1, W, H) and _in_bounds(x2, y2, W, H):
                color = (matplotlib.colors.hsv_to_rgb([ie / float(len(hand_edges)), 1.0, 1.0]) * 255.0).astype(np.uint8)
                color = (int(color[0]), int(color[1]), int(color[2]))
                cv2.line(canvas, (x1, y1), (x2, y2), color, thickness=2)

        for i in range(113, 134):
            if scores is not None and scores[i] < threshold: continue
            x, y = int(keypoints[i][0]), int(keypoints[i][1])
            if _in_bounds(x, y, W, H):
                cv2.circle(canvas, (x, y), 4, (0, 0, 255), thickness=-1)

    return canvas

def _extract_body(person, w, h):
    """从人物数据中提取身体关键点

    Args:
        person: 人物数据字典
        w: 图像宽度
        h: 图像高度

    Returns:
        tuple: (关键点坐标, 置信度分数)
    """
    pose_arr = _safe_array_3(person.get("pose_keypoints_2d", []), 18)
    pose_arr = _denorm_xy(pose_arr, w, h)
    scores = pose_arr[:, 2].copy()
    return pose_arr[:, :2], scores

def _extract_wholebody(person, w, h):
    """从人物数据中提取全身关键点

    Args:
        person: 人物数据字典
        w: 图像宽度
        h: 图像高度

    Returns:
        tuple: (关键点坐标, 置信度分数)
    """
    kps_all_flat = person.get("pose_keypoints_2d", [])
    num_points_in_json = len(kps_all_flat) // 3
    TARGET_POINTS = 134

    if num_points_in_json < TARGET_POINTS:
        kps_known = _safe_array_3(kps_all_flat, num_points_in_json)
        kps_all = np.zeros((TARGET_POINTS, 3), dtype=np.float32)
        kps_all[:num_points_in_json] = kps_known[:num_points_in_json]
    else:
        kps_all = _safe_array_3(kps_all_flat, TARGET_POINTS)

    # 反归一化所有关键点
    kps_all[:18]     = _denorm_xy(kps_all[:18],     w, h)
    kps_all[18:24]   = _denorm_xy(kps_all[18:24],   w, h)
    kps_all[24:92]   = _denorm_xy(kps_all[24:92],   w, h)
    kps_all[92:113]  = _denorm_xy(kps_all[92:113],  w, h)
    kps_all[113:134] = _denorm_xy(kps_all[113:134], w, h)

    scores = kps_all[:, 2].copy()
    return kps_all[:, :2], scores

class OLO_DrawPoseKeypoint:
    """绘制姿态关键点的节点"""

    @classmethod
    def INPUT_TYPES(cls):
        """定义节点输入类型

        Returns:
            dict: 输入类型定义
        """
        return {
            "required": {
                "pose_keypoint": ("POSE_KEYPOINT",),
                "score_threshold": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 1.0, "step": 0.01}),
                "scale_for_xinsr": ("BOOLEAN", {"default": False}),
                "keypoint_scheme": (["body", "wholebody"], {"default": "wholebody"}),
                "draw_all_people": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "base_image": ("IMAGE",),
                "overlay_alpha": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "draw"
    CATEGORY = "OLO/Pose"

    def draw(self, pose_keypoint, score_threshold, scale_for_xinsr, keypoint_scheme,
             draw_all_people, base_image=None, overlay_alpha=1.0):
        """绘制姿态关键点

        Args:
            pose_keypoint: 姿态关键点数据
            score_threshold: 置信度阈值
            scale_for_xinsr: 是否根据图像大小调整线条粗细
            keypoint_scheme: 关键点方案 (body 或 wholebody)
            draw_all_people: 是否绘制所有人
            base_image: 基础图像
            overlay_alpha: 叠加透明度

        Returns:
            tuple: 绘制后的图像
        """
        if isinstance(pose_keypoint, dict):
            pose_keypoint = [pose_keypoint]
        if not isinstance(pose_keypoint, list):
            pose_keypoint = []

        if len(pose_keypoint) == 0:
            pose_keypoint = [{"people": [], "canvas_width": 512, "canvas_height": 512}]

        num_frames = len(pose_keypoint)

        base_imgs_np = None
        if base_image is not None:
            base_imgs_np = (base_image.cpu().numpy() * 255.0).astype(np.uint8)
            if base_imgs_np.shape[0] != num_frames:
                if base_imgs_np.shape[0] == 1:
                    base_imgs_np = np.repeat(base_imgs_np[0:1], num_frames, axis=0)
                else:
                    base_imgs_np = np.repeat(base_imgs_np[:1], num_frames, axis=0)

        frames_out = []
        for t in range(num_frames):
            frame = pose_keypoint[t] if isinstance(pose_keypoint[t], dict) else {}
            w = int(frame.get("canvas_width", 512))
            h = int(frame.get("canvas_height", 512))
            people = frame.get("people", [])

            if base_imgs_np is not None:
                base = base_imgs_np[t]
                if base.shape[1] != w or base.shape[0] != h:
                    base = cv2.resize(base, (w, h), interpolation=cv2.INTER_AREA)
                canvas = base.copy()
            else:
                canvas = np.zeros((h, w, 3), dtype=np.uint8)

            persons = people if draw_all_people else (people[:1] if people else [])

            for person in persons:
                if keypoint_scheme == "body":
                    kps_xy, scores = _extract_body(person, w, h)
                    canvas = draw_body17_keypoints_openpose_style(
                        canvas, kps_xy, scores,
                        threshold=score_threshold,
                        scale_for_xinsr=scale_for_xinsr
                    )
                else:
                    kps_xy, scores = _extract_wholebody(person, w, h)
                    canvas = draw_wholebody_keypoints_openpose_style(
                        canvas, kps_xy, scores,
                        threshold=score_threshold,
                        scale_for_xinsr=scale_for_xinsr
                    )

            if base_imgs_np is not None and overlay_alpha < 1.0:
                canvas = cv2.addWeighted(canvas, overlay_alpha, base_imgs_np[t], 1.0 - overlay_alpha, 0)

            frames_out.append(canvas)

        result_tensor = torch.from_numpy(np.stack(frames_out, axis=0).astype(np.float32) / 255.0)
        return (result_tensor,)

NODE_CLASS_MAPPINGS = {"OLO_DrawPoseKeypoint": OLO_DrawPoseKeypoint}
NODE_DISPLAY_NAME_MAPPINGS = {"OLO_DrawPoseKeypoint": "OLO_DrawPoseKeypoint"}
