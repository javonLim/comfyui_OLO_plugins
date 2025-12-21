// OLO_Code节点修复扩展
// 用于实现动态输入输出端口管理和update按钮功能

import { app } from '../../../../scripts/app.js';

// 注册节点类型扩展
app.registerExtension({
    name: "OLO.OLO_Code_Fix",
    async setup() {
        console.log("[OLO_Code_Fix] Setup complete");
    },

    // 在节点创建时注册自定义行为
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 检查是否是OLO_Code节点
        if (nodeData.name === "OLO_Code") {
            console.log("[OLO_Code_Fix] Processing OLO_Code node definition");

            // 节点创建时的初始化函数
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated || function() {};

            nodeType.prototype.onNodeCreated = function() {
                // 调用原始方法
                originalOnNodeCreated.apply(this, arguments);

                console.log("[OLO_Code_Fix] onNodeCreated called for node", this.id);

                // 确保widgets数组存在
                if (!this.widgets) {
                    this.widgets = [];
                }

                // 初始更新输入和输出端口
                this._updateInputPorts();
                this._updateOutputPorts();

                // 添加Update和Reset按钮
                this._addUpdateButtons();

                // 移除定期检查，改为手动点击Update按钮更新
            };

            // 更新输入端口的方法（修复：确保端口数量正确）
            nodeType.prototype._updateInputPorts = function() {
                try {
                    console.log("[OLO_Code_Fix] Updating input ports");

                    // 查找inputcount widget
                    const inputcountWidget = this.widgets.find(w => w.name === "inputcount");
                    if (!inputcountWidget) {
                        console.error("[OLO_Code_Fix] inputcountWidget not found");
                        return;
                    }

                    // 获取inputcount值
                    const inputcount = parseInt(inputcountWidget.value) || 1;
                    console.log("[OLO_Code_Fix] inputcount value:", inputcount);

                    // 1. 先移除所有现有的in*输入端口
                    this.inputs = this.inputs.filter(input =>
                        !input.name || !input.name.startsWith("in")
                    );
                    console.log("[OLO_Code_Fix] Removed all existing in* input ports");

                    // 2. 重新添加所需数量的输入端口
                    for (let i = 0; i < inputcount; i++) {
                        this.addInput(`in${i}`, "*", { tooltip: `输入${i}` });
                        console.log("[OLO_Code_Fix] Added input port", i);
                    }

                    // 重新计算节点大小
                    if (this.setSizeForTextures) {
                        this.setSizeForTextures();
                    }

                    console.log("[OLO_Code_Fix] Successfully updated input ports to count:", inputcount);
                } catch (error) {
                    console.error("[OLO_Code_Fix] Error updating input ports:", error);
                }
            };

            // 更新输出端口的方法
            nodeType.prototype._updateOutputPorts = function() {
                try {
                    console.log("[OLO_Code_Fix] Updating output ports");

                    // 查找outputcount widget - 调试所有widget信息
                    console.log("[OLO_Code_Fix] All widgets:", this.widgets.map(w => ({name: w.name, label: w.label, type: w.type})));

                    // 查找outputcount widget - 尝试多种方式
                    let outputcountWidget = this.widgets.find(w =>
                        w.name === "outputcount" ||
                        w.label === "outputcount" ||
                        w.type === "number" && (w.name === "outputcount" || w.label === "outputcount")
                    );

                    // 如果找到，获取值；否则默认值为1
                    let outputcount = 1;
                    if (outputcountWidget) {
                        outputcount = parseInt(outputcountWidget.value) || 1;
                        console.log("[OLO_Code_Fix] Found outputcountWidget with value:", outputcountWidget.value, "parsed to:", outputcount);
                    } else {
                        console.error("[OLO_Code_Fix] outputcountWidget not found, using default value 1");
                    }

                    // 确保outputs数组存在
                    if (!this.outputs) {
                        this.outputs = [];
                        console.error("[OLO_Code_Fix] outputs array is undefined, cannot update");
                        return;
                    }

                    console.log("[OLO_Code_Fix] Total outputs available:", this.outputs.length);

                    // 对于OLO_Code节点，我们需要特殊处理：
                    // 1. 移除所有现有的输出端口
                    while (this.outputs.length > 0) {
                        this.removeOutput(0);
                    }

                    console.log("[OLO_Code_Fix] Removed all existing output ports");

                    // 2. 根据outputcount重新添加输出端口
                    for (let i = 0; i < outputcount; i++) {
                        this.addOutput(`output_${i}`, "*", { tooltip: `输出${i}` });
                        console.log("[OLO_Code_Fix] Added output port", i);
                    }

                    // 重新计算节点大小
                    if (this.setSizeForTextures) {
                        this.setSizeForTextures();
                    }

                    // 触发节点更新事件，确保UI正确刷新
                    if (this.graph) {
                        this.graph.setDirtyCanvas(true, true);
                    }

                    console.log("[OLO_Code_Fix] Successfully updated output ports to count:", outputcount);
                } catch (error) {
                    console.error("[OLO_Code_Fix] Error updating output ports:", error);
                }
            };

            // 监听参数值变化，自动更新输入和输出端口
            const originalOnConfigure = nodeType.prototype.onConfigure || function() {};
            nodeType.prototype.onConfigure = function() {
                originalOnConfigure.apply(this, arguments);
                this._updateInputPorts();
                this._updateOutputPorts();
                // 不要在这里调用_addUpdateButton，避免重复添加
            };

            // 添加Update和Reset按钮到节点
            nodeType.prototype._addUpdateButtons = function() {
                try {
                    console.log("[OLO_Code_Fix] Adding Update and Reset buttons");

                    // 移除所有现有的按钮
                    this.widgets = this.widgets.filter(widget =>
                        widget.type !== "button"
                    );

                    // 添加Update按钮
                    this.addWidget("button", "Update ports", null, () => {
                        console.log("[OLO_Code_Fix] Update button clicked");
                        this._updateInputPorts();
                        this._updateOutputPorts();
                    });

                    // 添加Reset按钮
                    this.addWidget("button", "Reset ports", null, () => {
                        console.log("[OLO_Code_Fix] Reset button clicked");

                        // 重置inputcount和outputcount为默认值
                        const inputcountWidget = this.widgets.find(w => w.name === "inputcount");
                        const outputcountWidget = this.widgets.find(w => w.name === "outputcount");

                        if (inputcountWidget) {
                            inputcountWidget.value = 1; // 默认值
                        }

                        if (outputcountWidget) {
                            outputcountWidget.value = 1; // 默认值
                        }

                        // 更新端口配置
                        this._updateInputPorts();
                        this._updateOutputPorts();
                    });

                    console.log("[OLO_Code_Fix] Successfully added Update and Reset buttons");
                } catch (error) {
                    console.error("[OLO_Code_Fix] Error adding buttons:", error);
                }
            };
        }
    },

    // 当节点被添加到画布时，确保输入和输出端口显示正确
    nodeCreated(node) {
        if (node.comfyClass === "OLO_Code") {
            console.log("[OLO_Code_Fix] nodeCreated called for node", node.id);

            // 定义同时更新输入和输出端口的函数
            const updatePorts = () => {
                if (node._updateInputPorts) {
                    node._updateInputPorts();
                }
                if (node._updateOutputPorts) {
                    node._updateOutputPorts();
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
