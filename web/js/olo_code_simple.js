// OLO_Code_Simple节点扩展
// 为OLO_Code_Simple节点添加Update按钮和动态输入端口功能

import { app } from '../../../../scripts/app.js';

app.registerExtension({
    name: "OLO.OLO_Code_Simple",
    async setup() {
        console.log("[OLO_Code_Simple] Setup complete");
    },

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "OLO_Code_Simple") {
            console.log("[OLO_Code_Simple] Processing OLO_Code_Simple node definition");

            // 重写onNodeCreated方法，确保Update按钮能显示
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated || function() {};

            nodeType.prototype.onNodeCreated = function() {
                // 调用原始方法
                originalOnNodeCreated.apply(this, arguments);

                console.log("[OLO_Code_Simple] onNodeCreated called for node", this.id);

                // 确保widgets数组存在
                if (!this.widgets) {
                    this.widgets = [];
                }

                // 初始更新输入端口
                this._updateInputPorts();

                // 添加定期检查，确保输入端口显示正确
                setInterval(() => {
                    this._updateInputPorts();
                }, 1000);
            };

            // 更新输入端口的方法
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
                    console.error("[OLO_Code_Simple] Error updating input ports:", error);
                }
            };

            // 监听参数值变化，自动更新输入端口
            const originalOnConfigure = nodeType.prototype.onConfigure || function() {};
            nodeType.prototype.onConfigure = function() {
                originalOnConfigure.apply(this, arguments);
                this._updateInputPorts();
            };
        }
    },

    // 当节点被添加到画布时，确保输入端口显示正确
    nodeCreated(node) {
        if (node.comfyClass === "OLO_Code_Simple") {
            console.log("[OLO_Code_Simple] nodeCreated called for node", node.id);

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
