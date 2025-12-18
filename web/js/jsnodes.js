import { app } from '../../scripts/app.js';

// 自定义OLO_Code节点UI处理
app.registerExtension({
    name: "OLO.OLO_Code",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "OLO_Code") {
            // 保存原始的onNodeCreated方法
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            // 重写onNodeCreated方法，添加输入端口调整UI
            nodeType.prototype.onNodeCreated = function() {
                // 调用原始方法
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }

                console.log("[OLO_Code] onNodeCreated called, widgets before add:", this.widgets?.length || 0);

                // 查找是否已有Update按钮
                const hasUpdateButton = this.widgets?.some(w => w.name === "Update") || false;
                console.log("[OLO_Code] Has Update button:", hasUpdateButton);

                // 只有在没有Update按钮时才添加
                if (!hasUpdateButton) {
                    // 添加更新按钮
                    console.log("[OLO_Code] Adding Update button");
                    const button = this.addWidget("button", "Update", null, () => {
                        console.log("[OLO_Code] Update button clicked");
                        this._updateInputPorts();
                        this._updateOutputPorts(); // 同时更新输出端口
                    });
                    console.log("[OLO_Code] Added button:", button);
                }

                // 初始更新输入端口和输出端口
                this._updateInputPorts();
                this._updateOutputPorts();

                console.log("[OLO_Code] onNodeCreated completed, widgets after add:", this.widgets?.length || 0);
            };

            // 添加更新输入端口方法
            nodeType.prototype._updateInputPorts = function() {
                try {
                    console.log("[OLO_Code] _updateInputPorts called");

                    // 确保widgets存在
                    if (!this.widgets) {
                        console.log("[OLO_Code] widgets not found in _updateInputPorts");
                        return;
                    }

                    // 查找inputcount widget
                    const inputcountWidget = this.widgets.find(w => w.name === "inputcount");
                    if (!inputcountWidget) {
                        console.log("[OLO_Code] inputcountWidget not found");
                        return;
                    }

                    // 获取inputcount值
                    const inputcount = parseInt(inputcountWidget.value) || 1;
                    console.log("[OLO_Code] inputcount:", inputcount);

                    // 移除现有的in0-in7输入
                    this.inputs = this.inputs.filter(input => !input.name || !input.name.startsWith("in"));
                    console.log("[OLO_Code] Removed old inputs, remaining:", this.inputs.length);

                    // 添加对应数量的输入端口
                    for (let i = 0; i < inputcount; i++) {
                        this.addInput(`in${i}`, "*", { tooltip: `输入${i}` });
                    }
                    console.log("[OLO_Code] Added new inputs, total:", this.inputs.length);

                    // 重新计算节点大小
                    if (this.setSizeForTextures) {
                        this.setSizeForTextures();
                    }
                } catch (error) {
                    console.error("[OLO_Code] Error in _updateInputPorts:", error);
                }
            };

            // 添加更新输出端口方法
            nodeType.prototype._updateOutputPorts = function() {
                try {
                    console.log("[OLO_Code] _updateOutputPorts called");

                    // 确保widgets存在
                    if (!this.widgets) {
                        console.log("[OLO_Code] widgets not found in _updateOutputPorts");
                        return;
                    }

                    // 查找outputcount widget
                    const outputcountWidget = this.widgets.find(w => w.name === "outputcount");
                    if (!outputcountWidget) {
                        console.log("[OLO_Code] outputcountWidget not found");
                        return;
                    }

                    // 获取outputcount值
                    const outputcount = parseInt(outputcountWidget.value) || 1;
                    console.log("[OLO_Code] outputcount:", outputcount);

                    // 查找节点元素
                    const nodeElement = document.getElementById(`node-${this.id}`);
                    if (!nodeElement) {
                        console.log("[OLO_Code] nodeElement not found for node", this.id);
                        return;
                    }

                    // 查找所有输出端口
                    const allItems = nodeElement.querySelectorAll('.item');
                    console.log("[OLO_Code] Found", allItems.length, "total items");

                    const outputPorts = Array.from(allItems).filter(item => {
                        return item.textContent && item.textContent.includes('output');
                    });
                    console.log("[OLO_Code] Found", outputPorts.length, "output ports");

                    // 根据outputcount显示/隐藏输出端口
                    outputPorts.forEach((port, index) => {
                        if (index < outputcount) {
                            port.style.display = 'flex';
                            port.style.visibility = 'visible';
                            console.log("[OLO_Code] Showing port", index);
                        } else {
                            port.style.display = 'none';
                            port.style.visibility = 'hidden';
                            console.log("[OLO_Code] Hiding port", index);
                        }
                    });

                    // 重新计算节点大小
                    if (this.setSizeForTextures) {
                        this.setSizeForTextures();
                    }
                } catch (error) {
                    console.error("[OLO_Code] Error in _updateOutputPorts:", error);
                }
            };

            // 监听outputcount变化，自动更新输出端口
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function() {
                console.log("[OLO_Code] onExecuted called");
                if (onExecuted) {
                    onExecuted.apply(this, arguments);
                }
                this._updateInputPorts();
                this._updateOutputPorts(); // 同时更新输出端口
            };
        }
    }
});
