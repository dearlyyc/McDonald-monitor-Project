import os
import winshell
from win32com.client import Dispatch

def create_startup_shortcut():
    # 專案路徑
    project_dir = r"D:\coding projects\McDonald monitor Project"
    bat_path = os.path.join(project_dir, "start_app.bat")
    
    # 啟動資料夾 (Startup)
    startup_path = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_path, "McDonald_Monitor_Launcher.lnk")
    
    print(f"欲建立捷徑於: {shortcut_path}")
    
    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = bat_path
        shortcut.WorkingDirectory = project_dir
        # 0 = Hidden, 1 = Normal, 7 = Minimized
        shortcut.WindowStyle = 7 # 最小化啟動，避免擋住螢幕，但仍可在工作列看到
        shortcut.IconLocation = os.path.join(project_dir, "favicon.ico") if os.path.exists(os.path.join(project_dir, "favicon.ico")) else ""
        shortcut.save()
        print("✅ 捷徑已成功加入 Windows 啟動清單！")
    except Exception as e:
        print(f"❌ 建立捷徑失敗: {e}")

if __name__ == "__main__":
    create_startup_shortcut()
