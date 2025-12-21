import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
import "./fabric.min.js";

function dataURLToBlob(dataurl) {
    var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    while(n--){
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], {type:mime});
}

const connect_keypoints = [
	[0, 1],   [1, 2],  [2, 3],   [3, 4],
	[1, 5],   [5, 6],  [6, 7],   [1, 8],
	[8, 9],   [9, 10], [1, 11],  [11, 12],
	[12, 13], [14, 0], [14, 16], [15, 0],
	[15, 17]
]

const connect_color = [
	[  0,   0, 255],
	[255,   0,   0],
	[255, 170,   0],
	[255, 255,   0],
	[255,  85,   0],
	[170, 255,   0],
	[ 85, 255,   0],
	[  0, 255,   0],

	[  0, 255,  85],
	[  0, 255, 170],
	[  0, 255, 255],
	[  0, 170, 255],
	[  0,  85, 255],
	[ 85,   0, 255],

	[170,   0, 255],
	[255,   0, 255],
	[255,   0, 170],
	[255,   0,  85]
]

const DEFAULT_KEYPOINTS = [
  [241,  77], [241, 120], [191, 118], [177, 183],
  [163, 252], [298, 118], [317, 182], [332, 245],
  [225, 241], [213, 359], [215, 454], [270, 240],
  [282, 360], [286, 456], [232,  59], [253,  60],
  [225,  70], [260,  72]
]

async function readFileToText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = async () => {
            resolve(reader.result);
        };
        reader.onerror = async () => {
            reject(reader.error);
        }
        reader.readAsText(file);
    })
}

async function loadImageAsync(imageURL) {
    return new Promise((resolve) => {
        const e = new Image();
        e.setAttribute('crossorigin', 'anonymous');
        e.addEventListener("load", () => { resolve(e); });
        e.src = imageURL;
        return e;
    });
}

async function canvasToBlob(canvas) {
    return new Promise(function(resolve) {
        canvas.toBlob(resolve);
    });
}

class OpenPosePanel {
    node = null;
	canvas = null;
	canvasElem = null
	panel = null

	undo_history = []
	redo_history = []

	visibleEyes = true;
	flipped = false;
	lockMode = false;

    constructor(panel, node) {
        this.panel = panel;
        this.node = node;
        this.canvasWidth = 512;
        this.canvasHeight = 768;
        this.nextPoseId = 0;
        this.backgroundImage = null;
        this.currentPoseFilter = -1; // -1 表示显示所有姿态

        this.createCanvas();
        this.createControls();
        this.setupEventHandlers();
        this.loadInitialPose();
    }

    createCanvas() {
        this.canvasElem = document.createElement('canvas');
        this.canvasElem.width = this.canvasWidth;
        this.canvasElem.height = this.canvasHeight;
        this.canvas = new fabric.Canvas(this.canvasElem, {
            backgroundColor: '#333333',
            selection: false
        });

        this.panel.element.appendChild(this.canvasElem);
        this.resizeCanvas(this.canvasWidth, this.canvasHeight);
    }

    createControls() {
        const controlsDiv = document.createElement('div');
        controlsDiv.style.position = 'absolute';
        controlsDiv.style.top = '10px';
        controlsDiv.style.left = '10px';
        controlsDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
        controlsDiv.style.padding = '10px';
        controlsDiv.style.borderRadius = '5px';
        controlsDiv.style.color = 'white';

        // 添加控制按钮
        const addPoseBtn = document.createElement('button');
        addPoseBtn.textContent = 'Add Pose';
        addPoseBtn.onclick = () => this.addNewPose();
        controlsDiv.appendChild(addPoseBtn);

        const clearBtn = document.createElement('button');
        clearBtn.textContent = 'Clear All';
        clearBtn.onclick = () => this.clearAll();
        controlsDiv.appendChild(clearBtn);

        const undoBtn = document.createElement('button');
        undoBtn.textContent = 'Undo';
        undoBtn.onclick = () => this.undo();
        controlsDiv.appendChild(undoBtn);

        const redoBtn = document.createElement('button');
        redoBtn.textContent = 'Redo';
        redoBtn.onclick = () => this.redo();
        controlsDiv.appendChild(redoBtn);

        // 添加背景图像按钮
        const bgImageBtn = document.createElement('button');
        bgImageBtn.textContent = 'Load Background';
        bgImageBtn.onclick = () => this.loadBackgroundImage();
        controlsDiv.appendChild(bgImageBtn);

        const clearBgBtn = document.createElement('button');
        clearBgBtn.textContent = 'Clear Background';
        clearBgBtn.onclick = () => this.clearBackgroundImage();
        controlsDiv.appendChild(clearBgBtn);

        // 添加姿态过滤控件
        const filterLabel = document.createElement('label');
        filterLabel.textContent = 'Pose Filter: ';
        filterLabel.style.marginLeft = '10px';
        controlsDiv.appendChild(filterLabel);

        const filterSelect = document.createElement('select');
        filterSelect.id = 'poseFilter';
        filterSelect.onchange = (e) => this.filterPoses(parseInt(e.target.value));

        const allOption = document.createElement('option');
        allOption.value = '-1';
        allOption.textContent = 'All Poses';
        filterSelect.appendChild(allOption);

        controlsDiv.appendChild(filterSelect);
        this.poseFilterSelect = filterSelect;

        this.panel.element.appendChild(controlsDiv);
    }

    setupEventHandlers() {
        this.canvas.on('path:created', (e) => {
            this.saveState();
        });

        this.canvas.on('object:modified', (e) => {
            this.saveState();
        });

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'z') {
                this.undo();
                e.preventDefault();
            } else if (e.ctrlKey && e.key === 'y') {
                this.redo();
                e.preventDefault();
            }
        });
    }

    loadInitialPose() {
        // 检查是否有保存的姿态数据
        if (this.node.properties.savedPose && this.node.properties.savedPose.trim() !== "") {
            this.loadJSON(this.node.properties.savedPose);
        } else {
            // 使用默认姿态
            const default_pose_keypoints_2d = [];
            DEFAULT_KEYPOINTS.forEach(pt => {
                default_pose_keypoints_2d.push(pt[0], pt[1], 1.0);
            });
            const defaultPeople = [{ "pose_keypoints_2d": default_pose_keypoints_2d }];
            this.setPose(defaultPeople);
        }

        // 加载背景图像
        if (this.node.properties.backgroundImage && this.node.properties.backgroundImage.trim() !== "") {
            this.loadBackgroundImageFromURL(this.node.properties.backgroundImage);
        }
    }

    async loadBackgroundImage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                try {
                    // 将图像转换为base64
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const dataURL = event.target.result;
                        this.setBackgroundImage(dataURL);

                        // 保存到节点属性
                        this.node.properties.backgroundImage = dataURL;
                        if (this.node.bgImageWidget) {
                            this.node.bgImageWidget.value = dataURL;
                        }
                    };
                    reader.readAsDataURL(file);
                } catch (error) {
                    console.error('Error loading background image:', error);
                }
            }
        };
        input.click();
    }

    async loadBackgroundImageFromURL(imageURL) {
        try {
            const img = await loadImageAsync(imageURL);
            fabric.Image.fromURL(imageURL, (fabricImg) => {
                this.setBackgroundImageObject(fabricImg);
            });
        } catch (error) {
            console.error('Error loading background image from URL:', error);
        }
    }

    setBackgroundImage(dataURL) {
        fabric.Image.fromURL(dataURL, (img) => {
            this.setBackgroundImageObject(img);
        });
    }

    setBackgroundImageObject(img) {
        // 调整图像大小以适应画布
        const canvasRatio = this.canvas.width / this.canvas.height;
        const imgRatio = img.width / img.height;

        let scaleX, scaleY;
        if (imgRatio > canvasRatio) {
            // 图像更宽，以宽度为准
            scaleX = this.canvas.width / img.width;
            scaleY = scaleX;
        } else {
            // 图像更高，以高度为准
            scaleY = this.canvas.height / img.height;
            scaleX = scaleY;
        }

        img.set({
            scaleX: scaleX,
            scaleY: scaleY,
            left: (this.canvas.width - img.width * scaleX) / 2,
            top: (this.canvas.height - img.height * scaleY) / 2,
            selectable: false,
            evented: false,
            _isBackground: true
        });

        // 移除旧背景
        if (this.backgroundImage) {
            this.canvas.remove(this.backgroundImage);
        }

        // 添加新背景到画布底层
        this.canvas.add(img);
        this.canvas.sendToBack(img);
        this.backgroundImage = img;
        this.canvas.renderAll();
    }

    clearBackgroundImage() {
        if (this.backgroundImage) {
            this.canvas.remove(this.backgroundImage);
            this.backgroundImage = null;
            this.canvas.renderAll();

            // 清除节点属性
            this.node.properties.backgroundImage = "";
            if (this.node.bgImageWidget) {
                this.node.bgImageWidget.value = "";
            }
        }
    }

    updatePoseFilterOptions() {
        // 获取所有姿态ID
        const poseIds = new Set();
        this.canvas.getObjects('circle').forEach(circle => {
            poseIds.add(circle._poseId);
        });

        // 清空现有选项（除了"All Poses"）
        while (this.poseFilterSelect.options.length > 1) {
            this.poseFilterSelect.remove(1);
        }

        // 添加姿态选项
        Array.from(poseIds).sort((a, b) => a - b).forEach(poseId => {
            const option = document.createElement('option');
            option.value = poseId;
            option.textContent = `Pose ${poseId + 1}`;
            this.poseFilterSelect.appendChild(option);
        });

        // 设置当前选中的过滤值
        this.poseFilterSelect.value = this.currentPoseFilter;
    }

    filterPoses(poseId) {
        this.currentPoseFilter = poseId;

        // 显示或隐藏姿态
        this.canvas.getObjects().forEach(obj => {
            if (obj._poseId !== undefined) {
                // 如果是姿态对象（圆形或线条）
                if (poseId === -1) {
                    // 显示所有姿态
                    obj.visible = true;
                } else {
                    // 只显示选中的姿态
                    obj.visible = obj._poseId === poseId;
                }
            }
        });

        this.canvas.renderAll();
    }

    addNewPose() {
        const pose_keypoints_2d = [];
        DEFAULT_KEYPOINTS.forEach(pt => {
            pose_keypoints_2d.push(pt[0], pt[1], 1.0);
        });
        this.addPose(pose_keypoints_2d);
    }

    clearAll() {
        this.canvas.clear();
        this.canvas.backgroundColor = '#333333';
        this.nextPoseId = 0;
        this.undo_history = [];
        this.redo_history = [];
    }

    saveState() {
        const state = JSON.stringify(this.canvas.toJSON());
        this.undo_history.push(state);
        if (this.undo_history.length > 20) {
            this.undo_history.shift();
        }
        this.redo_history = [];
    }

    undo() {
        if (this.undo_history.length > 0) {
            const state = this.undo_history.pop();
            this.redo_history.push(JSON.stringify(this.canvas.toJSON()));
            this.canvas.loadFromJSON(state, () => {
                this.canvas.renderAll();
            });
        }
    }

    redo() {
        if (this.redo_history.length > 0) {
            const state = this.redo_history.pop();
            this.undo_history.push(JSON.stringify(this.canvas.toJSON()));
            this.canvas.loadFromJSON(state, () => {
                this.canvas.renderAll();
            });
        }
    }

    resizeCanvas(width, height) {
        this.canvasWidth = width;
        this.canvasHeight = height;
        this.canvas.setDimensions({ width: width, height: height });
        this.canvas.renderAll();
    }

    loadJSON(jsonString) {
        try {
            const data = JSON.parse(jsonString);
            if (data.people && data.people.length > 0) {
                this.clearAll();
                data.people.forEach(person => {
                    if (person.pose_keypoints_2d) {
                        this.addPose(person.pose_keypoints_2d);
                    }
                });
            }
            return null;
        } catch (e) {
            return e.message;
        }
    }

    setPose(people) {
        this.clearAll();
        if (people && people.length > 0) {
            people.forEach(person => {
                if (person.pose_keypoints_2d) {
                    this.addPose(person.pose_keypoints_2d);
                }
            });
        }
    }

    addPose(pose_keypoints_2d = []) {
        const poseId = this.nextPoseId++;
        const circles = {};
        const lines = [];

        // 创建关节点
        for (let i = 0; i < 18; i++) {
            const x = pose_keypoints_2d[i * 3];
            const y = pose_keypoints_2d[i * 3 + 1];
            const confidence = pose_keypoints_2d[i * 3 + 2];

            if (confidence > 0) {
                const circle = new fabric.Circle({
                    radius: 5,
                    fill: `rgb(${connect_color[i][0]}, ${connect_color[i][1]}, ${connect_color[i][2]})`,
                    left: x - 5,
                    top: y - 5,
                    selectable: true,
                    hasControls: false,
                    _poseId: poseId,
                    _keypointIndex: i,
                    _id: i
                });
                circles[i] = circle;
                this.canvas.add(circle);
            }
        }

        // 创建连接线
        connect_keypoints.forEach((connection, index) => {
            const [startIdx, endIdx] = connection;
            if (circles[startIdx] && circles[endIdx]) {
                const line = new fabric.Line(
                    [
                        circles[startIdx].left + 5,
                        circles[startIdx].top + 5,
                        circles[endIdx].left + 5,
                        circles[endIdx].top + 5
                    ],
                    {
                        stroke: `rgb(${connect_color[index][0]}, ${connect_color[index][1]}, ${connect_color[index][2]})`,
                        strokeWidth: 3,
                        selectable: false,
                        evented: false,
                        _poseId: poseId,
                        _startCircle: circles[startIdx],
                        _endCircle: circles[endIdx]
                    }
                );
                lines.push(line);
                this.canvas.add(line);
            }
        });

        // 添加移动事件监听器
        Object.values(circles).forEach(circle => {
            circle.on('moving', () => {
                lines.forEach(line => {
                    if (line._startCircle === circle || line._endCircle === circle) {
                        line.set({
                            x1: line._startCircle.left + 5,
                            y1: line._startCircle.top + 5,
                            x2: line._endCircle.left + 5,
                            y2: line._endCircle.top + 5
                        });
                    }
                });
                this.canvas.renderAll();
            });
        });

        // 更新姿态过滤器选项
        this.updatePoseFilterOptions();

        // 应用当前过滤器
        this.filterPoses(this.currentPoseFilter);

        this.canvas.renderAll();
    }

    serializeJSON() {
        const allCircles = this.canvas.getObjects('circle');
        const poses = {};

        // 按姿态ID分组
        allCircles.forEach(circle => {
            const poseId = circle._poseId;
            if (!poses[poseId]) {
                poses[poseId] = [];
            }
            poses[poseId].push(circle);
        });

        const people = [];
        Object.keys(poses).sort((a, b) => a - b).forEach(poseId => {
            const poseCircles = poses[poseId];
            const keypoints_2d = new Array(18 * 3).fill(0);

            poseCircles.forEach(circle => {
                const pointId = circle._id;
                const center = circle.getCenterPoint();
                keypoints_2d[pointId * 3] = center.x;
                keypoints_2d[pointId * 3 + 1] = center.y;
                keypoints_2d[pointId * 3 + 2] = 1.0;
            });

            people.push({
                "pose_keypoints_2d": keypoints_2d
            });
        });

        return JSON.stringify({
                "width": this.canvas.width,
                "height": this.canvas.height,
                "people": people
        }, null, 4);
    }

    getPoses() {
        const poses = [];
        const poseGroups = {};

        // 按姿态ID分组
        this.canvas.getObjects('circle').forEach(circle => {
            const poseId = circle._poseId;
            if (!poseGroups[poseId]) {
                poseGroups[poseId] = [];
            }
            poseGroups[poseId][circle._keypointIndex] = {
                x: circle.left + 5,
                y: circle.top + 5,
                visible: circle.visible
            };
        });

        // 转换为OpenPose格式
        Object.values(poseGroups).forEach(keypoints => {
            const pose_keypoints_2d = [];
            for (let i = 0; i < 18; i++) {
                if (keypoints[i] && keypoints[i].visible) {
                    pose_keypoints_2d.push(keypoints[i].x, keypoints[i].y, 1.0);
                } else {
                    pose_keypoints_2d.push(0, 0, 0);
                }
            }
            poses.push({
                pose_keypoints_2d: pose_keypoints_2d,
                face_keypoints_2d: [],
                hand_left_keypoints_2d: [],
                hand_right_keypoints_2d: []
            });
        });

        return {
            people: poses,
            canvas_width: this.canvasWidth,
            canvas_height: this.canvasHeight
        };
    }
}

// 添加面板拖动功能
function makePanelDraggable(panelElement, openPosePanel) {
    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;

    const header = panelElement.querySelector(".dialog-header") || panelElement;
    header.style.userSelect = 'none';
    header.style.cursor = "move";

    header.addEventListener("mousedown", (e) => {
        isDragging = true;
        document.body.style.userSelect = "none";
    });

    window.addEventListener("mousemove", (e) => {
        if (isDragging) {
            const rectPanel = panelElement.getBoundingClientRect();

            if( rectPanel.left < document.querySelector('.side-tool-bar-container').offsetWidth && e.movementX < 0 ){
                panelElement.style.left = `${rectPanel.width / 2}px)`;
            } else if( rectPanel.left + rectPanel.width > window.innerWidth && e.movementX > 0 ){
                panelElement.style.left = `${window.innerWidth - rectPanel.width}px)`;
            } else {
                offsetX -= e.movementX;
                panelElement.style.left = `calc( 50% - ${offsetX}px)`;
            }

            if( rectPanel.top < document.querySelector('.comfyui-menu').offsetHeight && e.movementY < 0 ){
                panelElement.style.top = `${rectPanel.height / 2}px)`;
            } else if( rectPanel.top + rectPanel.height > window.innerHeight && e.movementY > 0 ){
                panelElement.style.left = `${window.innerWidth - rectPanel.height}px)`;
            } else {
                offsetY -= e.movementY;
                panelElement.style.top = `calc( 50% - ${offsetY}px)`;
            }
        }
    });

    window.addEventListener("mouseup", () => {
        isDragging = false;
        document.body.style.userSelect = "";
    });
}

app.registerExtension({
    name: "OLO.OpenposeEditor",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "OLO_OpenposeEditor") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // 确保属性存在
                if (!this.properties) {
                    this.properties = {};
                }
                if (!this.properties.savedPose) {
                    this.properties.savedPose = "";
                }
                if (!this.properties.backgroundImage) {
                    this.properties.backgroundImage = "";
                }

                this.serialize_widgets = true;

                // 图像组件
                this.imageWidget = this.widgets.find(w => w.name === "image");
                if (this.imageWidget) {
                    this.imageWidget.callback = this.showImage.bind(this);
                    this.imageWidget.disabled = true;
                }

                // 隐藏的文本组件
                this.jsonWidget = this.addWidget("text", "savedPose", this.properties.savedPose, "savedPose");
                if (this.jsonWidget && this.jsonWidget.inputEl) {
                    this.jsonWidget.inputEl.style.display = "none";
                }

                this.bgImageWidget = this.addWidget("text", "backgroundImage", this.properties.backgroundImage || "", () => {}, {});
                if (this.bgImageWidget && this.bgImageWidget.inputEl) {
                    this.bgImageWidget.inputEl.style.display = "none";
                }

                // 打开编辑器按钮
                this.openWidget = this.addWidget("button", "open editor", "image", () => {
                    const graphCanvas = LiteGraph.LGraphCanvas.active_canvas;
                    if (graphCanvas == null) return;

                    const panel = graphCanvas.createPanel("OLO OpenPose Editor", { closable: true });
                    panel.node = this;
                    panel.classList.add("openpose-editor");

                    this.openPosePanel = new OpenPosePanel(panel, this);
                    makePanelDraggable(panel, this.openPosePanel);
                    document.body.appendChild(this.openPosePanel.panel);

                    // 添加关闭事件处理
                    panel.onClose = () => {
                        // 保存姿态数据
                        const poses = this.openPosePanel.getPoses();
                        const poseJson = JSON.stringify(poses);

                        // 更新节点的savedPose属性
                        this.properties.savedPose = poseJson;

                        // 更新widget值
                        if (this.jsonWidget) {
                            this.jsonWidget.value = poseJson;
                        }

                        // 触发节点更新
                        app.graph.setDirtyCanvas(true);
                    };

                    // 添加调整大小功能
                    const resizer = document.createElement("div");
                    resizer.style.width = "10px";
                    resizer.style.height = "10px";
                    resizer.style.background = "#888";
                    resizer.style.position = "absolute";
                    resizer.style.right = "0";
                    resizer.style.bottom = "0";
                    resizer.style.cursor = "se-resize";
                    panel.appendChild(resizer);

                    let isResizing = false;
                    resizer.addEventListener("mousedown", (e) => {
                        e.preventDefault();
                        isResizing = true;
                    });

                    document.addEventListener("mousemove", (e) => {
                        if (!isResizing) return;
                        const rect = panel.getBoundingClientRect();
                        panel.style.width = `${e.clientX - rect.left}px`;
                        panel.style.height = `${e.clientY - rect.top}px`;
                    });

                    document.addEventListener("mouseup", () => {
                        isResizing = false;
                        this.openPosePanel.resizeCanvas();
                    });
                });
                this.openWidget.serialize = false;

                // 属性变化处理
                const baseOnPropertyChanged = nodeType.prototype.onPropertyChanged;
                nodeType.prototype.onPropertyChanged = function (property, value, prev) {
                    if (property === "savedPose" && this.jsonWidget) {
                        this.jsonWidget.value = value;
                    } else if (property === "backgroundImage" && this.bgImageWidget) {
                        this.bgImageWidget.value = value;
                    } else if (baseOnPropertyChanged) {
                        baseOnPropertyChanged.call(this, property, value, prev);
                    }
                };

                return r;
            }

            // 图像显示方法
            nodeType.prototype.showImage = async function(name) {
                let folder_separator = name.lastIndexOf("/");
                let subfolder = "";
                if (folder_separator > -1) {
                    subfolder = name.substring(0, folder_separator);
                    name = name.substring(folder_separator + 1);
                }
                const img = await loadImageAsync(`/view?filename=${name}&type=input&subfolder=${subfolder}&t=${Date.now()}`);
                this.imgs = [img];
                app.graph.setDirtyCanvas(true);
            }

            nodeType.prototype.setImage = async function(name) {
                if (this.imageWidget) {
                    this.imageWidget.value = name;
                    await this.showImage(name);
                }
            }

            // 添加菜单项
            const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
            nodeType.prototype.getExtraMenuOptions = function (_, options) {
                getExtraMenuOptions?.apply(this, arguments);
                options.unshift({
                    content: "Open in OLO OpenPose Editor",
                    callback: () => {
                        this.openWidget?.callback();
                    },
                });
            }
        }
    }
});
