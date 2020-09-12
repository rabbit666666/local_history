import wx

wx.Log.SetLogLevel(0)

DARK_COLOR1 = wx.Colour(79, 79, 79)
DARK_COLOR2 = wx.Colour(51, 51, 51)
DARK_COLOR3 = wx.Colour(88, 88, 88)

class CodePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(79, 79, 79))

        self.imageCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.SUNKEN_BORDER | wx.TE_READONLY)
        font1 = wx.Font(11, wx.MODERN, wx.NORMAL, wx.NORMAL, False, 'Consolas')
        self.imageCtrl.SetBackgroundColour(wx.BLACK)
        self.imageCtrl.SetForegroundColour(wx.GREEN)
        self.imageCtrl.SetFont(font1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.imageCtrl, 1, wx.EXPAND | wx.ALL)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, _evt):
        self.Show(False)

    def SetInfo(self, info):
        self.imageCtrl.SetValue(info)
