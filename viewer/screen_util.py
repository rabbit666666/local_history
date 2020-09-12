import wx

def get_screen_scale():
	scale = wx.ScreenDC().GetPPI()[0] / 96.0
	return scale

def dpi_scale(size):
	scale = get_screen_scale()
	if isinstance(size, tuple):
		width = size[0] > 0 and size[0] * scale or size[0]
		height = size[1] > 0 and size[1] * scale or size[1]
		new_size = (width, height)
	else:
		new_size = size * scale
	return new_size