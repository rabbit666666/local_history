import wx

def show_dialog(title, msg):
    dlg = wx.MessageDialog(None, msg, title, wx.OK)
    dlg.ShowModal()
    dlg.Destroy()
