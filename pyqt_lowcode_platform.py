#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoBot极简低代码平台 - PyQt版本
基于PyQt5实现的可视化工作流编辑器
"""

import sys
import json
import math
from typing import Dict, List, Any, Tuple
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QLabel, QFrame, QDialog, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QDialogButtonBox,
    QMessageBox, QFileDialog, QStatusBar, QSplitter, QCheckBox
)
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette
from Autobot import AutoBot

class Node:
    """节点类"""
    def __init__(self, node_id: str, node_type: str, x: int, y: int):
        self.id = node_id
        self.type = node_type
        self.x = x
        self.y = y
        self.width = 120
        self.height = 60
        self.params = {}
        self.selected = False
        self.hovered = False

    def contains_point(self, x: int, y: int) -> bool:
        """检查点是否在节点内"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)

    def get_center(self) -> Tuple[int, int]:
        """获取节点中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)

class Connection:
    """连接类"""
    def __init__(self, from_node: str, to_node: str):
        self.from_node = from_node
        self.to_node = to_node

class ParameterDialog(QDialog):
    """参数设置对话框"""
    def __init__(self, parent, node_type: str, current_params: Dict = None):
        super().__init__(parent)
        self.node_type = node_type
        self.current_params = current_params or {}
        self.result_params = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"设置 {self.node_type} 参数")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 参数表单
        form_layout = QFormLayout()
        self.param_widgets = {}
        
        # 根据节点类型创建参数输入控件 - 对应函数的实际参数
        param_configs = {
            'click_left': [
                ('img', '目标图片路径', 'str', 'target.png'),
                ('retry', '重试次数', 'int', 1)
            ],
            'double_click': [
                ('img', '目标图片路径', 'str', 'target.png'),
                ('retry', '重试次数', 'int', 1)
            ],
            'click_right': [
                ('img', '目标图片路径', 'str', 'target.png'),
                ('retry', '重试次数', 'int', 1)
            ],
            'input_text': [
                ('text', '输入文本', 'str', 'Hello World'),
                ('clear', '是否清空原文本', 'bool', False)
            ],
            'wait': [
                ('seconds', '等待时间(秒)', 'float', 1.0)
            ],
            'scroll': [
                ('amount', '滚动量(正上负下)', 'int', 100),
                ('repeat', '重复次数', 'int', 1)
            ],
            'hotkey': [
                ('keys', '热键组合(如ctrl+c)', 'str', 'ctrl+c'),
                ('repeat', '重复次数', 'int', 1)
            ],
            'for_loop': [
                ('loop_count', '循环次数', 'int', 3),
                ('loop_name', '循环名称', 'str', '循环1')
            ],
            'loop_end': [
                ('end_name', '结束标记名称', 'str', '循环结束')
            ]
        }
        
        if self.node_type in param_configs:
            for param_name, label, param_type, default_value in param_configs[self.node_type]:
                current_value = self.current_params.get(param_name, default_value)
                widget = self.create_param_widget(param_type, current_value)
                self.param_widgets[param_name] = widget
                form_layout.addRow(label + ':', widget)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_params)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def create_param_widget(self, param_type: str, default_value):
        """创建参数输入控件"""
        if param_type == 'int':
            widget = QSpinBox()
            widget.setRange(-9999, 9999)
            widget.setValue(int(default_value))
            return widget
        elif param_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(0.0, 999.0)
            widget.setValue(float(default_value))
            return widget
        elif param_type == 'bool':
            widget = QCheckBox()
            widget.setChecked(bool(default_value))
            return widget
        else:  # str
            widget = QLineEdit()
            widget.setText(str(default_value))
            return widget
    
    def accept_params(self):
        """保存参数"""
        self.result_params = {}
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QSpinBox):
                self.result_params[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                self.result_params[param_name] = widget.value()
            elif isinstance(widget, QCheckBox):
                self.result_params[param_name] = widget.isChecked()
            else:  # QLineEdit
                self.result_params[param_name] = widget.text()
        self.accept()

class Canvas(QWidget):
    """画布组件"""
    node_double_clicked = pyqtSignal(str)  # 节点双击信号
    connection_mode_exit = pyqtSignal()  # 连接模式退出信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        
        # 数据
        self.nodes: Dict[str, Node] = {}
        self.connections: List[Connection] = []
        
        # 交互状态
        self.dragging_node = None
        self.drag_offset = QPoint(0, 0)
        self.connecting_mode = False
        self.delete_mode = False
        self.connection_start = None
        
        # 样式
        self.setStyleSheet("background-color: #f8f9fa;")
        
    def add_node(self, node_id: str, node_type: str, x: int = None, y: int = None):
        """添加节点"""
        if x is None:
            x = 50 + len(self.nodes) * 150
        if y is None:
            y = 100
            
        node = Node(node_id, node_type, x, y)
        self.nodes[node_id] = node
        self.update()
        
    def remove_node(self, node_id: str):
        """删除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # 删除相关连接
            self.connections = [conn for conn in self.connections 
                              if conn.from_node != node_id and conn.to_node != node_id]
            self.update()
    
    def add_connection(self, from_node: str, to_node: str):
        """添加连接"""
        if from_node != to_node and from_node in self.nodes and to_node in self.nodes:
            # 检查是否已存在连接
            for conn in self.connections:
                if conn.from_node == from_node and conn.to_node == to_node:
                    return
            self.connections.append(Connection(from_node, to_node))
            self.update()
    
    def get_node_at_pos(self, x: int, y: int) -> str:
        """获取指定位置的节点"""
        for node_id, node in self.nodes.items():
            if node.contains_point(x, y):
                return node_id
        return None
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制连接线
        self.draw_connections(painter)
        
        # 绘制节点
        self.draw_nodes(painter)
        
    def draw_nodes(self, painter: QPainter):
        """绘制节点"""
        for node in self.nodes.values():
            # 节点颜色配置
            colors = {
                'click_left': '#4CAF50',
                'double_click': '#2196F3', 
                'click_right': '#FF9800',
                'input_text': '#9C27B0',
                'wait': '#607D8B',
                'scroll': '#795548',
                'hotkey': '#E91E63',
                'for_loop': '#FF5722',
                'loop_end': '#9E9E9E'
            }
            
            base_color = QColor(colors.get(node.type, '#757575'))
            
            # 设置画笔和画刷
            if node.selected:
                pen = QPen(QColor('#2196F3'), 3)
            elif node.hovered:
                pen = QPen(QColor('#2196F3'), 2)
            else:
                pen = QPen(QColor('#e0e0e0'), 1)
                
            painter.setPen(pen)
            painter.setBrush(QBrush(base_color))
            
            # 绘制节点矩形
            rect = QRect(node.x, node.y, node.width, node.height)
            painter.drawRoundedRect(rect, 8, 8)
            
            # 绘制节点文本
            painter.setPen(QPen(QColor('white')))
            painter.setFont(QFont('Arial', 10, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, node.type)
            
            # 绘制参数指示器
            if node.params:
                painter.setPen(QPen(QColor('#FFC107')))
                painter.setBrush(QBrush(QColor('#FFC107')))
                indicator_rect = QRect(node.x + node.width - 15, node.y + 5, 10, 10)
                painter.drawEllipse(indicator_rect)
    
    def draw_connections(self, painter: QPainter):
        """绘制连接线"""
        painter.setPen(QPen(QColor('#666666'), 2))
        
        for conn in self.connections:
            if conn.from_node in self.nodes and conn.to_node in self.nodes:
                from_node = self.nodes[conn.from_node]
                to_node = self.nodes[conn.to_node]
                
                # 计算连接点
                from_x, from_y = from_node.get_center()
                to_x, to_y = to_node.get_center()
                
                # 绘制箭头线
                painter.drawLine(from_x, from_y, to_x, to_y)
                
                # 绘制箭头
                angle = math.atan2(to_y - from_y, to_x - from_x)
                arrow_length = 15
                arrow_angle = math.pi / 6
                
                arrow_x1 = to_x - arrow_length * math.cos(angle - arrow_angle)
                arrow_y1 = to_y - arrow_length * math.sin(angle - arrow_angle)
                arrow_x2 = to_x - arrow_length * math.cos(angle + arrow_angle)
                arrow_y2 = to_y - arrow_length * math.sin(angle + arrow_angle)
                
                painter.drawLine(to_x, to_y, int(arrow_x1), int(arrow_y1))
                painter.drawLine(to_x, to_y, int(arrow_x2), int(arrow_y2))
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            node_id = self.get_node_at_pos(x, y)
            
            if node_id:
                if self.delete_mode:
                    # 删除节点
                    self.remove_node(node_id)
                elif self.connecting_mode:
                    if self.connection_start is None:
                        self.connection_start = node_id
                    else:
                        self.add_connection(self.connection_start, node_id)
                        self.connection_start = None
                        # 每次连接后自动退出连接模式
                        self.connecting_mode = False
                        # 发送信号通知主窗口更新按钮状态
                        self.connection_mode_exit.emit()
                else:
                    # 开始拖拽
                    node = self.nodes[node_id]
                    self.dragging_node = node_id
                    self.drag_offset = QPoint(x - node.x, y - node.y)
                    
                    # 设置选中状态
                    for n in self.nodes.values():
                        n.selected = False
                    node.selected = True
                    self.update()
            else:
                # 点击空白区域，取消选中
                for node in self.nodes.values():
                    node.selected = False
                self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        x, y = event.x(), event.y()
        
        if self.dragging_node:
            # 拖拽节点
            node = self.nodes[self.dragging_node]
            node.x = x - self.drag_offset.x()
            node.y = y - self.drag_offset.y()
            self.update()
        else:
            # 更新悬浮状态
            hovered_node = self.get_node_at_pos(x, y)
            
            for node_id, node in self.nodes.items():
                old_hovered = node.hovered
                node.hovered = (node_id == hovered_node)
                if old_hovered != node.hovered:
                    self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging_node = None
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            node_id = self.get_node_at_pos(x, y)
            if node_id:
                self.node_double_clicked.emit(node_id)

class PyQtLowCodePlatform(QMainWindow):
    """PyQt低代码平台主窗口"""
    
    def __init__(self):
        super().__init__()
        self.node_counter = 0
        self.autobot = AutoBot()
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("AutoBot极简低代码平台 - PyQt版")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧工具栏
        self.setup_sidebar(splitter)
        
        # 右侧画布区域
        self.setup_canvas_area(splitter)
        
        # 设置分割器比例
        splitter.setSizes([250, 950])
        
        # 状态栏
        self.setup_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def setup_sidebar(self, parent):
        """设置侧边栏"""
        sidebar = QFrame()
        sidebar.setFrameStyle(QFrame.StyledPanel)
        sidebar.setMaximumWidth(250)
        
        layout = QVBoxLayout(sidebar)
        
        # 标题
        title = QLabel("功能模块")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # 功能按钮
        functions = [
            ('click_left', '左键点击', '#4CAF50'),
            ('double_click', '双击', '#2196F3'),
            ('click_right', '右键点击', '#FF9800'),
            ('input_text', '输入文本', '#9C27B0'),
            ('wait', '等待', '#607D8B'),
            ('scroll', '滚动', '#795548'),
            ('hotkey', '热键', '#E91E63'),
            ('for_loop', 'For循环', '#FF5722'),
            ('loop_end', '循环结束', '#9E9E9E')
        ]
        
        for func_name, display_name, color in functions:
            btn = QPushButton(display_name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 12px;
                    margin: 5px;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color, 0.8)};
                }}
            """)
            btn.clicked.connect(lambda checked, name=func_name: self.add_node(name))
            layout.addWidget(btn)
        

        layout.addStretch()
        
        # 控制按钮
        control_layout = QVBoxLayout()
        
        self.connect_btn = QPushButton("连接模式")
        self.connect_btn.setCheckable(True)
        self.connect_btn.clicked.connect(self.toggle_connection_mode)
        
        self.delete_btn = QPushButton("删除模式")
        self.delete_btn.setCheckable(True)
        self.delete_btn.clicked.connect(self.toggle_delete_mode)
        
        run_btn = QPushButton("运行工作流")
        run_btn.clicked.connect(self.run_workflow)
        
        save_btn = QPushButton("保存工作流")
        save_btn.clicked.connect(self.save_workflow)
        
        load_btn = QPushButton("加载工作流")
        load_btn.clicked.connect(self.load_workflow)
        
        clear_btn = QPushButton("清空画布")
        clear_btn.clicked.connect(self.clear_canvas)
        
        for btn in [self.connect_btn, self.delete_btn, run_btn, save_btn, load_btn, clear_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: none;
                    padding: 10px;
                    margin: 3px;
                    border-radius: 6px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                }
                QPushButton:checked {
                    background-color: #e74c3c;
                }
            """)
            control_layout.addWidget(btn)
        
        layout.addLayout(control_layout)
        parent.addWidget(sidebar)
    
    def setup_canvas_area(self, parent):
        """设置画布区域"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 创建画布
        self.canvas = Canvas()
        self.canvas.node_double_clicked.connect(self.edit_node_parameters)
        self.canvas.connection_mode_exit.connect(self.on_connection_mode_exit)
        
        scroll_area.setWidget(self.canvas)
        parent.addWidget(scroll_area)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
            }
        """)
    
    def add_node(self, node_type: str):
        """添加节点"""
        self.node_counter += 1
        node_id = f"node_{self.node_counter}"
        self.canvas.add_node(node_id, node_type)
        self.update_status()
    
    def edit_node_parameters(self, node_id: str):
        """编辑节点参数"""
        if node_id in self.canvas.nodes:
            node = self.canvas.nodes[node_id]
            dialog = ParameterDialog(self, node.type, node.params)
            
            if dialog.exec_() == QDialog.Accepted and dialog.result_params is not None:
                node.params = dialog.result_params
                self.canvas.update()
                QMessageBox.information(self, "成功", f"已保存 {node.type} 的参数配置")
    
    def toggle_connection_mode(self):
        """切换连接模式"""
        # 如果开启连接模式，关闭删除模式
        if self.connect_btn.isChecked():
            self.delete_btn.setChecked(False)
            self.canvas.delete_mode = False
        
        self.canvas.connecting_mode = self.connect_btn.isChecked()
        self.canvas.connection_start = None
        
        if self.canvas.connecting_mode:
            self.status_bar.showMessage("连接模式：点击两个节点来创建连接")
        else:
            self.status_bar.showMessage("就绪")
    
    def toggle_delete_mode(self):
        """切换删除模式"""
        # 如果开启删除模式，关闭连接模式
        if self.delete_btn.isChecked():
            self.connect_btn.setChecked(False)
            self.canvas.connecting_mode = False
            self.canvas.connection_start = None
        
        self.canvas.delete_mode = self.delete_btn.isChecked()
        
        if self.canvas.delete_mode:
            self.status_bar.showMessage("删除模式：点击节点来删除")
        else:
            self.status_bar.showMessage("就绪")
    
    def update_status_for_mode_change(self):
        """更新模式变化后的状态"""
        if self.canvas.connecting_mode:
            self.status_bar.showMessage("连接模式：点击两个节点来创建连接")
        elif self.canvas.delete_mode:
            self.status_bar.showMessage("删除模式：点击节点来删除")
        else:
            self.status_bar.showMessage("就绪")
    
    def on_connection_mode_exit(self):
        """处理连接模式退出信号"""
        self.connect_btn.setChecked(False)
        self.update_status_for_mode_change()
    
    def run_workflow(self):
        """运行工作流"""
        if not self.canvas.nodes:
            QMessageBox.warning(self, "警告", "画布上没有节点")
            return
        
        # 立即最小化窗口
        self.showMinimized()
        
        # 找到起始节点（没有输入连接的节点）
        start_nodes = []
        for node_id in self.canvas.nodes:
            has_input = any(conn.to_node == node_id for conn in self.canvas.connections)
            if not has_input:
                start_nodes.append(node_id)
        
        if not start_nodes:
            # 恢复窗口显示以显示警告
            self.showNormal()
            QMessageBox.warning(self, "警告", "没有找到起始节点")
            return
        
        # 执行工作流
        executed = set()
        for start_node in start_nodes:
            self.execute_from_node(start_node, executed)
        
        # 恢复窗口显示以显示完成消息
        self.showNormal()
        QMessageBox.information(self, "完成", "工作流执行完成")
    
    def execute_from_node(self, node_id: str, executed: set):
        """从指定节点开始执行"""
        if node_id in executed or node_id not in self.canvas.nodes:
            return
        
        executed.add(node_id)
        node = self.canvas.nodes[node_id]
        
        # 检查是否为for_loop节点
        if node.type == 'for_loop':
            loop_count = node.params.get('loop_count', 3)
            loop_name = node.params.get('loop_name', '循环1')
            
            # 获取循环体的所有节点路径
            loop_body_paths = self.find_loop_body_paths(node_id)
            
            # 执行循环
            for i in range(loop_count):
                print(f"执行 {loop_name} 第 {i+1}/{loop_count} 次")
                # 为每次循环执行完整的循环体路径
                for path in loop_body_paths:
                    for path_node in path:
                        if path_node in self.canvas.nodes:
                            node_obj = self.canvas.nodes[path_node]
                            if node_obj.type != 'loop_end':  # 不执行loop_end节点
                                self.execute_node_operation(node_obj)
            
            # 循环执行完毕后，查找loop_end节点并继续执行其后续节点
            self.execute_after_loop(node_id, executed)
        else:
            # 执行普通节点操作
            self.execute_node_operation(node)
            
            # 执行后续节点
            for conn in self.canvas.connections:
                if conn.from_node == node_id:
                    self.execute_from_node(conn.to_node, executed)
    
    def find_loop_body_paths(self, loop_node_id: str):
        """找到循环体的所有执行路径（从for_loop到loop_end之间的节点）"""
        paths = []
        
        # 找到循环节点的直接后续节点作为起始点
        start_nodes = []
        for conn in self.canvas.connections:
            if conn.from_node == loop_node_id:
                start_nodes.append(conn.to_node)
        
        # 为每个起始节点构建执行路径，直到遇到loop_end节点
        for start_node in start_nodes:
            current_path = []
            self.build_execution_path_until_end(start_node, current_path, paths, set())
        
        return paths if paths else [[]]  # 如果没有路径，返回空路径列表
    
    def build_execution_path_until_end(self, node_id: str, current_path: list, all_paths: list, visited: set):
        """递归构建执行路径，直到遇到loop_end节点"""
        if node_id in visited or node_id not in self.canvas.nodes:
            return
        
        visited.add(node_id)
        current_path.append(node_id)
        
        # 检查是否为loop_end节点
        node = self.canvas.nodes[node_id]
        if node.type == 'loop_end':
            # 遇到循环结束节点，当前路径结束
            all_paths.append(current_path.copy())
            return
        
        # 找到当前节点的后续节点
        next_nodes = []
        for conn in self.canvas.connections:
            if conn.from_node == node_id:
                next_nodes.append(conn.to_node)
        
        if not next_nodes:  # 如果没有后续节点且不是loop_end，当前路径结束
            all_paths.append(current_path.copy())
        else:
            # 继续构建路径
            for next_node in next_nodes:
                self.build_execution_path_until_end(next_node, current_path, all_paths, visited.copy())
        
        current_path.pop()  # 回溯
    
    def execute_after_loop(self, loop_node_id: str, executed: set):
        """执行循环结束后的节点"""
        # 查找与此循环相关的loop_end节点
        loop_end_nodes = self.find_loop_end_nodes(loop_node_id)
        
        # 执行loop_end节点之后的节点
        for loop_end_id in loop_end_nodes:
            if loop_end_id not in executed:
                executed.add(loop_end_id)
                # 执行loop_end节点后续的所有节点
                for conn in self.canvas.connections:
                    if conn.from_node == loop_end_id:
                        self.execute_from_node(conn.to_node, executed)
    
    def find_loop_end_nodes(self, loop_node_id: str):
        """查找与指定循环节点相关的loop_end节点"""
        loop_end_nodes = []
        
        # 从循环节点开始，递归查找所有可达的loop_end节点
        visited = set()
        self.search_loop_end_nodes(loop_node_id, loop_end_nodes, visited)
        
        return loop_end_nodes
    
    def search_loop_end_nodes(self, node_id: str, loop_end_nodes: list, visited: set):
        """递归搜索loop_end节点"""
        if node_id in visited or node_id not in self.canvas.nodes:
            return
        
        visited.add(node_id)
        node = self.canvas.nodes[node_id]
        
        # 如果是loop_end节点，添加到结果中
        if node.type == 'loop_end':
            loop_end_nodes.append(node_id)
            return  # 找到loop_end后停止搜索
        
        # 继续搜索后续节点
        for conn in self.canvas.connections:
            if conn.from_node == node_id:
                self.search_loop_end_nodes(conn.to_node, loop_end_nodes, visited)
    
    def execute_loop_body(self, node_id: str, executed: set):
        """执行循环体内的节点"""
        if node_id in executed or node_id not in self.canvas.nodes:
            return
        
        executed.add(node_id)
        node = self.canvas.nodes[node_id]
        
        # 如果遇到另一个for_loop节点，递归处理
        if node.type == 'for_loop':
            self.execute_from_node(node_id, executed)
        else:
            # 执行普通节点操作
            self.execute_node_operation(node)
            
            # 执行后续节点
            for conn in self.canvas.connections:
                if conn.from_node == node_id:
                    self.execute_loop_body(conn.to_node, executed)
    
    def execute_node_operation(self, node: Node):
        """执行节点操作"""
        try:
            if node.type == 'click_left':
                img = node.params.get('img', 'target.png')
                retry = node.params.get('retry', 1)
                self.autobot.click_left(img, retry)
            
            elif node.type == 'double_click':
                img = node.params.get('img', 'target.png')
                retry = node.params.get('retry', 1)
                self.autobot.double_click(img, retry)
            
            elif node.type == 'click_right':
                img = node.params.get('img', 'target.png')
                retry = node.params.get('retry', 1)
                self.autobot.click_right(img, retry)
            
            elif node.type == 'input_text':
                text = node.params.get('text', '')
                clear = node.params.get('clear', False)
                if text:
                    self.autobot.input_text(text, clear)
            
            elif node.type == 'wait':
                seconds = node.params.get('seconds', 1.0)
                self.autobot.wait(seconds)
            
            elif node.type == 'scroll':
                amount = node.params.get('amount', 100)
                repeat = node.params.get('repeat', 1)
                self.autobot.scroll(amount, repeat)
            
            elif node.type == 'hotkey':
                keys = node.params.get('keys', 'ctrl+c')
                repeat = node.params.get('repeat', 1)
                # 将热键字符串拆分成多个参数
                key_list = keys.replace('+', ',').split(',')
                key_list = [key.strip() for key in key_list]  # 去除空格
                for _ in range(repeat):
                    self.autobot.hotkey(*key_list)
            
            elif node.type == 'for_loop':
                # for_loop节点不执行具体操作，只是标记循环开始
                # 实际的循环逻辑在execute_from_node中处理
                pass
            
            elif node.type == 'loop_end':
                # loop_end节点本身不执行具体操作，仅作为循环结束的标记
                print(f"循环结束标记: {node.params.get('end_name', '循环结束')}")
                pass
                    
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"执行节点 {node.type} 时出错：{str(e)}")
    
    def save_workflow(self):
        """保存工作流"""
        filename, _ = QFileDialog.getSaveFileName(self, "保存工作流", "", "JSON Files (*.json)")
        if filename:
            try:
                workflow_data = {
                    'nodes': {
                        node_id: {
                            'type': node.type,
                            'x': node.x,
                            'y': node.y,
                            'params': node.params
                        }
                        for node_id, node in self.canvas.nodes.items()
                    },
                    'connections': [
                        {'from': conn.from_node, 'to': conn.to_node}
                        for conn in self.canvas.connections
                    ]
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(workflow_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", "工作流已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")
    
    def load_workflow(self):
        """加载工作流"""
        filename, _ = QFileDialog.getOpenFileName(self, "加载工作流", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                # 清空当前画布
                self.clear_canvas()
                
                # 加载节点
                for node_id, node_data in workflow_data.get('nodes', {}).items():
                    self.canvas.add_node(node_id, node_data['type'], node_data['x'], node_data['y'])
                    self.canvas.nodes[node_id].params = node_data.get('params', {})
                
                # 加载连接
                for conn_data in workflow_data.get('connections', []):
                    self.canvas.add_connection(conn_data['from'], conn_data['to'])
                
                # 更新节点计数器
                if self.canvas.nodes:
                    max_counter = max([int(node_id.split('_')[1]) for node_id in self.canvas.nodes.keys()])
                    self.node_counter = max_counter
                
                self.update_status()
                QMessageBox.information(self, "成功", "工作流已加载")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败：{str(e)}")
    
    def clear_canvas(self):
        """清空画布"""
        # 显示确认提示框
        reply = QMessageBox.question(self, "确认清空", "确定要清空画布吗？这将删除所有节点和连接。",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.canvas.nodes.clear()
            self.canvas.connections.clear()
            self.canvas.update()
            self.node_counter = 0
            self.update_status()
    
    def update_status(self):
        """更新状态栏"""
        node_count = len(self.canvas.nodes)
        conn_count = len(self.canvas.connections)
        self.status_bar.showMessage(f"就绪 | 节点数: {node_count} | 连接数: {conn_count}")
    
    def darken_color(self, color: str, factor: float = 0.9) -> str:
        """使颜色变暗"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = PyQtLowCodePlatform()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()