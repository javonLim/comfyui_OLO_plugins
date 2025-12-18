// OLO_Code节点修复扩展
// 修复Update按钮不显示和输出端口数量与outputcount参数不一致的问题

import { app } from '../../../../scripts/app.js';

app.registerExtension({
    name: "OLO.OLO_Code_Fix",
    async setup() {
        console.log("[OLO_Code_Fix] Setup complete");
    },

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "OLO_Code") {
            console.log("[OLO_Code_Fix] Processing OLO_Code node definition");

            // 重写onNodeCreated方法，确保Update按钮能显示
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

                // 添加定期检查，确保输入和输出端口显示正确
                setInterval(() => {
                    this._updateInputPorts();
                    this._updateOutputPorts();
                }, 1000);
            };

            // 更新输入端口的方法（原有功能）
            nodeType.prototype._updateInputPorts = function() {
                try {
                    // 查找inputcount widget
                    const inputcountWidget = this.widgets.find(w => w.name === "inputcount");
                    if (!inputcountWidget) return;

                    // 获取inputcount值
                    const inputcount = parseInt(inputcountWidget.value) || 1;

                    // 移除现有的in0-in7输入
                    this.inputs = this.inputs.filter(input => !input.name || !input.name.startsWith("in"));

                    // 添加对应数量的输入端口
                    for (let i = 0; i < inputcount; i++) {
                        this.addInput(`in${i}`, "*", { tooltip: `输入${i}` });
                    }

                    // 重新计算节点大小
                    if (this.setSizeForTextures) {
                        this.setSizeForTextures();
                    }
                } catch (error) {
                    console.error("[OLO_Code_Fix] Error updating input ports:", error);
                }
            };

            // 更新输出端口的方法（新增功能）
            nodeType.prototype._updateOutputPorts = function() {
                try {
                    console.log("[OLO_Code_Fix] Updating output ports");

                    // 查找outputcount widget
                    const outputcountWidget = this.widgets.find(w => w.name === "outputcount");
                    if (!outputcountWidget) {
                        console.error("[OLO_Code_Fix] outputcountWidget not found");
                        return;
                    }

                    // 获取outputcount值
                    const outputcount = parseInt(outputcountWidget.value) || 1;
                    console.log("[OLO_Code_Fix] outputcount value:", outputcount);

                    // 确保outputs数组存在
                    if (!this.outputs) {
                        this.outputs = [];
                    }

                    // 移除所有输出端口
                    while (this.outputs.length > 0) {
                        this.removeOutput(0);
                    }

                    // 添加指定数量的输出端口
                    for (let i = 0; i < outputcount; i++) {
                        this.addOutput(`output_${i}`, "*", { tooltip: `输出${i}` });
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
