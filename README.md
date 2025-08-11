# AutoPipeline Low-Code Platform User Guide

## Introduction

AutoPipeline is a visual low-code automation platform developed with PyQt5 that allows users to create automated workflows by dragging and dropping nodes, enabling various automation tasks without writing complex code.

## Main Features

### 🎯 Core Node Types

- **Mouse Operations**
  - Left Click: Click on specified image location
  - Double Click: Double-click on specified image location
  - Right Click: Right-click on specified image location

- **Text Input**
  - Input Text: Enter specified text into the current focus
  - Supports clear original text option (checkbox form)

- **System Operations**
  - Wait: Pause execution for specified seconds
  - Scroll: Mouse wheel scrolling
  - Hotkey: Execute keyboard shortcut combinations
  - Paste Time: Paste current timestamp
  - Execute Command: Run system commands

- **Flow Control**
  - For Loop: Repeat execution for specified number of times
  - Loop End: Mark loop boundaries and control loop range

### 🔧 Advanced Features

- **Visual Editor**: Intuitive node drag-and-drop interface
- **Connection Mode**: Define node execution order through connections
- **Parameter Configuration**: Double-click nodes to set detailed parameters
- **Workflow Save/Load**: Support JSON format workflow files
- **Real-time Execution**: One-click execution of entire workflow

## Quick Start

### 1. Launch Platform

```bash
python pyqt_lowcode_platform.py
```

### 2. Create Your First Workflow

1. **Add Nodes**
   - Click the desired node type in the left toolbar
   - Node will be automatically added to the center of the canvas

2. **Configure Node Parameters**
   - Double-click node to open parameter settings dialog
   - Configure corresponding parameters based on node type
   - Boolean parameters are presented as checkboxes

3. **Connect Nodes**
   - Click "Connection Mode" button
   - Click nodes in sequence (from start node to target node)
   - Right-click or press ESC to exit connection mode

4. **Execute Workflow**
   - Click "Execute" button to run the entire workflow
   - Observe console output to understand execution status

### 3. Save and Load Workflows

- **Save**: Click "Save Workflow" button, select save location
- **Load**: Click "Load Workflow" button, select saved JSON file

## Detailed Usage Instructions

### Node Parameter Configuration

#### Mouse Operation Nodes
- **Image File**: Target image filename (place in images folder)
- **Retry Count**: Number of retries when image search fails

#### Text Input Nodes
- **Text Content**: Text to be entered
- **Clear Original Text**: When checked, will first clear existing content in input box

#### Wait Nodes
- **Wait Time**: Number of seconds to pause (supports decimals)

#### Scroll Nodes
- **Scroll Amount**: Number of pixels to scroll (positive for up, negative for down)
- **Repeat Count**: Number of times to repeat scroll operation

#### Hotkey Nodes
- **Key Combination**: Comma-separated keys (e.g., ctrl,c)
- **Repeat Count**: Number of times to repeat hotkey operation

#### For Loop Nodes
- **Loop Count**: Number of times to execute loop
- **Loop Variable Name**: Variable name used in the loop

### For Loop Usage Method

1. **Add For Loop Node**
   - Set loop count and variable name

2. **Add Loop Body Nodes**
   - Add nodes to be repeatedly executed after the For Loop node

3. **Add Loop End Node**
   - Add "Loop End" node at the end of loop body
   - Mark the boundary range of the loop

4. **Connect Subsequent Nodes**
   - Continue adding other nodes after the "Loop End" node
   - These nodes will execute after the loop completes

### Workflow Execution Logic

- Workflow starts execution from nodes without preceding connections
- Execute nodes sequentially according to connection order
- For loops will repeatedly execute all nodes within the loop body
- Continue executing subsequent nodes after loop completion

## Best Practices

### 1. Image File Management
- Place all target images in the `images` folder
- Use clear, easily recognizable images
- Recommend using PNG format for best recognition results

### 2. Workflow Design
- Use wait nodes appropriately to ensure interface loading completion
- Set retry counts for critical operations
- Use descriptive node names for easier maintenance

### 3. Debugging Tips
- Test individual node functionality first
- Build complex workflows incrementally
- Observe console output to understand execution status

### 4. Error Handling
- Check if image files exist
- Confirm parameter configuration is correct
- Verify node connection relationships

## Common Issues

### Q: What to do when image recognition fails?
A: Check if image files exist in the images folder, ensure images are clear and consistent with screen display.

### Q: How to adjust mouse movement speed?
A: You can modify the `mouse_speed` parameter in Autobot.py.

### Q: Loop not executing as expected?
A: Ensure you've added a "Loop End" node to mark loop boundaries, check if node connections are correct.

### Q: Text input not working?
A: Ensure the target input box has focus, you can add a click operation first.

## Technical Support

If you encounter problems or need new features, please check the project documentation or submit feedback. AutoPipeline is continuously updated, committed to providing better automation experience.

---

**AutoPipeline** - Making automation simple and efficient!
