# ComfyUI-OLO_plugins

OLO插件是一个ComfyUI扩展，提供了多种实用节点，包括代码执行、姿态编辑等功能。

## 节点列表

### 代码执行节点

#### OLO_Code
- **功能**: 执行Python代码，支持动态输入输出端口
- **类别**: OLO/code
- **输入**: 
  - code: Python代码
  - inputcount: 输入端口数量
  - outputcount: 输出端口数量
  - input1, input2, ..., inputN: 动态输入端口
- **输出**: 
  - output1, output2, ..., outputN: 动态输出端口
- **特性**: 支持自动更新端口数量，无需手动点击Update按钮

### 姿态编辑节点

#### OLO_OpenposeEditor
- **功能**: OpenPose编辑器，用于创建和编辑姿态数据
- **类别**: OLO/pose
- **输入**: 
  - show_body, show_face, show_hands: 显示/隐藏身体、面部、手部
  - resolution_x: 分辨率X
  - pose_marker_size, face_marker_size, hand_marker_size: 标记大小
  - hands_scale, body_scale, head_scale, overall_scale: 缩放参数
  - POSE_JSON: 姿态JSON数据
  - POSE_KEYPOINT: 姿态关键点数据
- **输出**: 
  - POSE_IMAGE: 姿态图像
  - POSE_KEYPOINT: 姿态关键点
  - POSE_JSON: 姿态JSON数据
- **特性**: 支持在OpenPose编辑器中打开进行可视化编辑

#### OLO_OriginalOpenPoseEditor
- **功能**: 原始OpenPose编辑器，提供基础的姿态编辑功能
- **类别**: OLO/pose
- **输入**: 
  - image: 图像路径
- **输出**: 
  - IMAGE: 处理后的图像

#### OLO_AppendageEditor
- **功能**: 肢体编辑器，用于编辑身体各部分的姿态
- **类别**: OLO/pose
- **输入**: 
  - show_body, show_face, show_hands: 显示/隐藏身体、面部、手部
  - resolution_x: 分辨率X
  - pose_marker_size, face_marker_size, hand_marker_size: 标记大小
  - POSE_JSON: 姿态JSON数据
  - POSE_KEYPOINT: 姿态关键点数据
- **输出**: 
  - POSE_IMAGE: 姿态图像
  - POSE_KEYPOINT: 姿态关键点
  - POSE_JSON: 姿态JSON数据

#### OLO_OpenPoseEditorPlus
- **功能**: 增强版OpenPose编辑器，提供更多姿态编辑功能
- **类别**: OLO/pose
- **输入**: 
  - image: 图像路径
  - output_width_for_dwpose: DW Pose输出宽度
  - output_height_for_dwpose: DW Pose输出高度
  - scale_for_xinsr_for_dwpose: XINSR缩放
- **输出**: 
  - pose_image: 姿态图像
  - combined_image: 合成图像
  - dw_pose_image: DW Pose图像
  - dw_combined_image: DW合成图像

#### OLO_SavePoseToJson
- **功能**: 将姿态数据保存为JSON文件
- **类别**: OLO/pose
- **输入**: 
  - image: 图像
  - pose_keypoint: 姿态关键点
  - filename_prefix: 文件名前缀
- **输出**: 
  - filename: 保存的文件名

## 安装

1. 将此插件目录复制到ComfyUI的custom_nodes目录中
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 重启ComfyUI

## 使用说明

### OLO_Code节点使用示例

```python
# 简单加法示例
output1 = input1 + input2
```

### OpenPose编辑器使用

1. 添加OLO_OpenposeEditor节点到工作流
2. 右键点击节点，选择"Open in Openpose Editor"
3. 在编辑器中创建或编辑姿态
4. 点击Close按钮返回ComfyUI
5. 节点会自动更新姿态数据

## 更新日志

- 修复了OLO_Code节点输出端口数量不匹配问题
- 移除了OLO_Code节点的Update按钮，实现自动端口更新
- 迁移了ComfyUI-ultimate-openpose-editor的节点
- 迁移了ComfyUI-OpenPose-Editor-Plus的节点
- 添加了OLO_OriginalOpenPoseEditor节点

## 许可证

MIT License