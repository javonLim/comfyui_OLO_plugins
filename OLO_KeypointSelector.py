class OLO_KeypointSelector:
    """关键点帧选择器节点，用于处理姿态关键点数据"""
    
    @classmethod
    def INPUT_TYPES(cls):
        """定义节点输入类型
        
        Returns:
            dict: 输入类型定义
        """
        return {
            "required": {
                "pose_keypoint": ("POSE_KEYPOINT",),
                "frame_index": ("INT", {"default": 0, "min": 0, "step": 1}),
                "frame_index_rewrite": ("INT", {"default": 0, "min": 0, "step": 1}),
            },
            "optional": {
                "keypoint_frame_rewrite": ("POSE_KEYPOINT",),
            }
        }

    RETURN_TYPES = ("POSE_KEYPOINT", "POSE_KEYPOINT", "INT")
    RETURN_NAMES = ("pose_keypoint_updated", "pose_keypoint_single", "selected_frame_index")
    FUNCTION = "process"
    CATEGORY = "OLO/Pose"

    def process(self, pose_keypoint, frame_index, frame_index_rewrite, keypoint_frame_rewrite=None):
        """处理姿态关键点数据
        
        Args:
            pose_keypoint: 输入姿态关键点数据
            frame_index: 要选择的帧索引
            frame_index_rewrite: 要重写的帧索引
            keypoint_frame_rewrite: 用于重写的关键点帧数据
            
        Returns:
            tuple: (更新后的姿态关键点, 单帧姿态关键点, 选中的帧索引)
        """
        # 如果输入是人物列表（人物字典列表），将其包装为单帧以保留所有人物
        if isinstance(pose_keypoint, list) and len(pose_keypoint) > 0 and isinstance(pose_keypoint[0], dict):  
            person_keys = {
                "pose_keypoints_2d", "face_keypoints_2d",
                "hand_left_keypoints_2d", "hand_right_keypoints_2d",      
                "foot_keypoints_2d", "id"
            }
            if any(k in pose_keypoint[0] for k in person_keys):
                pose_keypoint = [{"people": pose_keypoint, "canvas_width": 512, "canvas_height": 768}]

        # 标准化为帧列表
        if not isinstance(pose_keypoint, list):
            pose_keypoint = [pose_keypoint]

        if len(pose_keypoint) == 0:  
            pose_keypoint = [{"people": [], "canvas_width": 512, "canvas_height": 768}]

        # 确保帧索引在有效范围内
        frame_index = max(0, min(frame_index, len(pose_keypoint) - 1))    
        frame_index_rewrite = max(0, min(frame_index_rewrite, len(pose_keypoint) - 1))

        # 提取选定的帧并确保它是带有人物列表的帧字典
        single_frame = pose_keypoint[frame_index]
        if isinstance(single_frame, dict) and not ("people" in single_frame and isinstance(single_frame.get("people"), list)):
            person_keys = {
                "pose_keypoints_2d", "face_keypoints_2d",
                "hand_left_keypoints_2d", "hand_right_keypoints_2d",      
                "foot_keypoints_2d", "id"
            }
            if any(k in single_frame for k in person_keys):
                single_frame = {     
                    "people": [single_frame],
                    "canvas_width": single_frame.get("canvas_width", 512),
                    "canvas_height": single_frame.get("canvas_height", 768)
                }
            else:
                single_frame = {     
                    "people": [],    
                    "canvas_width": single_frame.get("canvas_width", 512) if isinstance(single_frame, dict) else 512,
                    "canvas_height": single_frame.get("canvas_height", 768) if isinstance(single_frame, dict) else 768
                }

        # 创建更新后的姿态关键点列表
        updated = list(pose_keypoint)
        
        # 如果提供了重写数据，则标准化并重写
        if keypoint_frame_rewrite is not None:
            rewrite = keypoint_frame_rewrite
            if isinstance(rewrite, list) and len(rewrite) == 1:
                rewrite = rewrite[0] 
            if isinstance(rewrite, dict) and not ("people" in rewrite and isinstance(rewrite.get("people"), list)):
                person_keys = {
                    "pose_keypoints_2d", "face_keypoints_2d",
                    "hand_left_keypoints_2d", "hand_right_keypoints_2d",  
                    "foot_keypoints_2d", "id"
                }
                if any(k in rewrite for k in person_keys):
                    rewrite = {
                        "people": [rewrite],
                        "canvas_width": rewrite.get("canvas_width", 512),
                        "canvas_height": rewrite.get("canvas_height", 768)
                    }
                else:
                    rewrite = {
                        "people": [],
                        "canvas_width": rewrite.get("canvas_width", 512) if isinstance(rewrite, dict) else 512,
                        "canvas_height": rewrite.get("canvas_height", 768) if isinstance(rewrite, dict) else 768
                    }
            updated[frame_index_rewrite] = rewrite

        return (updated, single_frame, frame_index)

NODE_CLASS_MAPPINGS = {"OLO_KeypointSelector": OLO_KeypointSelector}
NODE_DISPLAY_NAME_MAPPINGS = {"OLO_KeypointSelector": "OLO_KeypointSelector"}