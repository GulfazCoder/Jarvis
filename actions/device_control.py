import subprocess
import os
import shutil
from pathlib import Path
import pyautogui
import psutil
import requests
import pyperclip
import logging
from typing import List, Dict, Any

# Setup logging for device control
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / 'device_control.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ShellExecutor:
    """Handles arbitrary shell command execution with user privileges."""

    @staticmethod
    def execute(command: str, capture_output: bool = True) -> Dict[str, Any]:
        logging.info(f"Executing shell command: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            logging.error(f"Command execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

class InputController:
    """Programmatic control of keyboard and mouse via pyautogui."""

    @staticmethod
    def move_mouse(x: int, y: int):
        logging.info(f"Moving mouse to {x}, {y}")
        pyautogui.moveTo(x, y)

    @staticmethod
    def click(x: int = None, y: int = None, button: str = 'left'):
        logging.info(f"Clicking {button} at {x}, {y}")
        pyautogui.click(x=x, y=y, button=button)

    @staticmethod
    def type_text(text: str):
        logging.info("Typing text")
        pyautogui.write(text)

    @staticmethod
    def press_key(key: str):
        logging.info(f"Pressing key: {key}")
        pyautogui.press(key)

    @staticmethod
    def hotkey(*keys: str):
        logging.info(f"Performing hotkey: {keys}")
        pyautogui.hotkey(*keys)

class NetworkManager:
    """Handles network operations and external data transmission."""

    @staticmethod
    def send_request(method: str, url: str, data: Any = None, headers: Dict = None) -> Dict[str, Any]:
        logging.info(f"Network request: {method} to {url}")
        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "content": response.text
            }
        except Exception as e:
            logging.error(f"Network request failed: {str(e)}")
            return {"success": False, "error": str(e)}

class SensitiveDataManager:
    """Accesses system-sensitive data like browser history and documents."""

    @staticmethod
    def get_browser_history(browser: str = 'chrome'):
        # This is a simplified pointer; actual implementation depends on browser paths
        logging.info(f"Attempting to access {browser} history")
        # Implementation would involve querying SQLite DBs in User AppData
        return {"info": "Browser history access requires specific path mapping for the OS."}

    @staticmethod
    def read_clipboard() -> str:
        logging.info("Reading clipboard")
        return pyperclip.paste()

    @staticmethod
    def write_clipboard(text: str):
        logging.info("Writing to clipboard")
        pyperclip.copy(text)

class SoftwareManager:
    """Handles software installation and removal."""

    @staticmethod
    def install_package(package_name: str, manager: str = 'pip'):
        logging.info(f"Installing {package_name} via {manager}")
        cmd = f"{manager} install {package_name}"
        return ShellExecutor.execute(cmd)

    @staticmethod
    def uninstall_package(package_name: str, manager: str = 'pip'):
        logging.info(f"Uninstalling {package_name} via {manager}")
        cmd = f"{manager} uninstall -y {package_name}"
        return ShellExecutor.execute(cmd)
