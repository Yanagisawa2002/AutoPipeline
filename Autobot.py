import pyautogui
import time
import pyperclip
import os
from typing import Union, List, Optional
from tqdm import *
import random

class AutoBot:
    def __init__(self):
        self.last_ad_check = 0
        self.AD_CHECK_INTERVAL = 5
        self.screen_width, self.screen_height = pyautogui.size()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_root = os.path.join(script_dir, "images")
        os.makedirs(self.image_root, exist_ok=True)
        self.mouse_speed = 0.5  # 默认移动速度（秒）
    
    #region 核心操作函数
    def click_left(self, img: str, retry: int = 1):
        """单击左键"""
        self._mouse_click(1, "left", img, retry)
        print(f"单击左键 [{img}]")

    def double_click(self, img: str, retry: int = 1):
        """双击左键"""
        self._mouse_click(2, "left", img, retry)
        print(f"双击左键 [{img}]")

    def click_right(self, img: str, retry: int = 1):
        """右键单击"""
        self._mouse_click(1, "right", img, retry)
        print(f"右键点击 [{img}]")

    def input_text(self, text: str, clear: bool = False):
        """输入文本"""
        if clear:
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
        
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        print(f"输入文本: {text} (清除原文本: {clear})")
        time.sleep(0.2)

    def wait(self, seconds: Union[int, float]):
        """等待指定秒数"""
        print(f"等待 {seconds} 秒")
        for _ in tqdm(range(seconds)):
            time.sleep(1)

    def scroll(self, amount: int, repeat: int = 1):
        """滚动鼠标滚轮"""
        for _ in range(repeat):
            pyautogui.scroll(amount)
            print(f"滚轮滚动 {amount} 单位")
            time.sleep(0.2)

    def hotkey(self, *keys: str, repeat: int = 1):
        """执行热键组合"""
        for _ in range(repeat):
            pyautogui.hotkey(*keys)
            print(f"热键操作: {'+'.join(keys)}")
            time.sleep(0.3)

    def paste_time(self, time_format: str = "%Y-%m-%d %H:%M:%S"):
        """粘贴当前时间"""
        localtime = time.strftime(time_format, time.localtime())
        pyperclip.copy(localtime)
        pyautogui.hotkey('ctrl', 'v')
        print(f"粘贴时间: {localtime}")

    def run_command(self, command: str):
        """执行系统命令"""
        os.system(command)
        print(f"执行系统命令: {command}")

    def silent_click(self, img: str, confidence: float = 0.8):
        """静默点击（找不到不报错）"""
        try:
            pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)
            if pos:
                pyautogui.click(pos)
                return True
        except Exception as e:
            pass
        return False

    #endregion


    #region 私有方法
    def _mouse_click(self, clicks: int, button: str, img: str, retry: int):
        """通用鼠标点击逻辑"""
        for _ in range(retry):
            location = pyautogui.locateCenterOnScreen(img, confidence=0.9)
            if location:
                pyautogui.click(
                    x=location.x,
                    y=location.y,
                    clicks=clicks,
                    interval=0.2,
                    duration=0.2,
                    button=button
                )
                break
            time.sleep(0.1)
    #endregion

# 初始化自动化机器人
# 注意：这个实例只在直接运行脚本时创建

def demo_workflow(bot, org):
    bot.click_left("url.png")
    bot.hotkey("enter")
    bot.wait(10)
    bot.hotkey("ctrl", "s") 
    bot.wait(2)
    bot.input_text(org+str(page))
    bot.wait(2)
    bot.hotkey("enter")
    bot.wait(2)

    