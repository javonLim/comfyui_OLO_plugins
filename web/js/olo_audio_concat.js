// OLO_AudioConcat节点的前端扩展文件
// 用于实现动态输入端口管理和update按钮功能

import { app } from "../../../../scripts/app.js";

// 注册节点类型扩展
app.registerExtension({
    name: "OLOAudioConcat", // 使用更独特的名称，避免与其他OLO节点冲突
    async setup() {
        console.log("[OLO_AudioConcat] Setup complete");
    },

    // 在节点创建时注册自定义行为
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 检查是否是OLO_AudioConcat节点
        if (nodeData.name === "OLO_AudioConcat") {
            console.log("[OLO_AudioConcat] Processing OLO_AudioConcat node definition");

            // 节点创建时的初始化函数
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated || function() {};

            nodeType.prototype.onNodeCreated = function() {
                // 调用原始方法
                originalOnNodeCreated.apply(this, arguments);

                console.log("[OLO_AudioConcat] onNodeCreated called for node", this.id);

                // 确保widgets数组存在
                if (!this.widgets) {
                    this.widgets = [];
                }

                // 存储原始输入端口类型
                this._audioType = "AUDIO";

                // 初始更新输入端口
                this._updateInputPorts();
            };

            // 更新输入端口的方法
            nodeType.prototype._updateInputPorts = function() {
                try {
                    // 查找inputcount widget
                    const inputcountWidget = this.widgets.find(w => w.name === "inputcount");
                    if (!inputcountWidget) {
                        console.error("[OLO_AudioConcat] 未找到inputcount widget");
                        return;
                    }

                    // 获取inputcount值
                    const inputcount = parseInt(inputcountWidget.value) || 2;
                    console.log(`[OLO_AudioConcat] 更新输入端口数量为: ${inputcount}`);

                    // 1. 处理widgets - 只更新mute toggle控件，不重新创建所有控件
                    // 先移除旧的mute toggle控件和update按钮
                    this.widgets = this.widgets.filter(widget => {
                        // 保留数值控件，移除mute toggle和update按钮
                        return widget.name === "inputcount" ||
                               widget.name === "start_spacer" ||
                               widget.name === "middle_spacer" ||
                               widget.name === "end_spacer";
                    });

                    // 2. 处理音频输入端口 - 只添加或删除，不重新创建所有端口
                    // 获取当前音频输入端口数量
                    const currentAudioInputs = this.inputs.filter(input =>
                        input.name && input.name.startsWith("audio_")
                    ).length;

                    if (currentAudioInputs < inputcount) {
                        // 需要添加新的音频输入端口
                        for (let i = currentAudioInputs + 1; i <= inputcount; i++) {
                            this.addInput(`audio_${i}`, this._audioType, {
                                label: `Audio ${i}`
                            });
                        }
                    } else if (currentAudioInputs > inputcount) {
                        // 需要移除多余的音频输入端口
                        // 从最后一个端口开始移除
                        for (let i = currentAudioInputs; i > inputcount; i--) {
                            // 找到要移除的端口索引
                            const portIndex = this.inputs.findIndex(input =>
                                input.name === `audio_${i}`
                            );
                            if (portIndex !== -1) {
                                this.removeInput(portIndex);
                            }
                        }
                    }

                    // 3. 添加mute toggle控件
                    for (let i = 1; i <= inputcount; i++) {
                        // 创建toggle widget来控制静音
                        this.addWidget("toggle", `mute_${i}`, false, (value) => {
                            console.log(`[OLO_AudioConcat] mute_${i} toggled to`, value);
                        }, {
                            label: `Mute Audio ${i}`
                        });
                    }

                    // 4. 在所有控件之后添加update按钮，确保它显示在最下面
                    this.addWidget("button", "Update inputs", null, () => {
                        console.log("[OLO_AudioConcat] Update button clicked");
                        this._updateInputPorts();
                    });

                    // 重新计算节点大小
                    if (this.setSizeForTextures) {
                        this.setSizeForTextures();
                    }

                    console.log(`[OLO_AudioConcat] 输入端口更新完成，当前数量: ${inputcount}`);
                } catch (error) {
                    console.error("[OLO_AudioConcat] 更新输入端口时出错:", error);
                }
            };

            // 重置方法，确保在节点加载时正确初始化端口
            const onConfigure = nodeType.prototype.onConfigure || function() {};
            nodeType.prototype.onConfigure = function(w) {
                // 调用原始方法
                onConfigure.apply(this, arguments);

                // 在配置完成后更新输入端口
                if (w && w.widgets_values) {
                    // 延迟执行，确保节点完全加载
                    setTimeout(() => {
                        this._updateInputPorts();
                    }, 100);
                }
            };
        }
    },

    // 当节点被添加到画布时，确保输入端口显示正确
    nodeCreated(node) {
        if (node.comfyClass === "OLO_AudioConcat") {
            console.log("[OLO_AudioConcat] nodeCreated called for node", node.id);

            // 定义更新输入端口的函数
            const updatePorts = () => {
                if (node._updateInputPorts) {
                    node._updateInputPorts();
                }
            };

            // 立即更新端口
            setTimeout(() => {
                updatePorts();
            }, 0);

            // 延迟更新，确保DOM完全渲染
            setTimeout(() => {
                updatePorts();
            }, 100);

            // 再次延迟更新，确保节点完全初始化
            setTimeout(() => {
                updatePorts();
            }, 500);
        }
    }
});
