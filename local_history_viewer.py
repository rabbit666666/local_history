import ctypes

import wx

from viewer import main_panel

if __name__ == "__main__":
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    app = wx.App(False)
    frame = main_panel.MainFrame()
    app.MainLoop()
