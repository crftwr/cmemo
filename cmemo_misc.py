import winreg

import ckit
from ckit.ckit_const import *
import pyauto

#--------------------------------------------------------------------

## IEのプロキシ設定を取得する
#
#  @return IEのプロキシ設定 ( "proxy.server.net:8080" のような形式 ) または プロキシ設定が無効な場合は None
#
def getIEProxySetting():

    proxy_setting = None

    reg_handle = None
    try:
        reg_handle = winreg.OpenKeyEx( winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings", 0, _winreg.KEY_READ )
        proxy_enable, reg_type = winreg.QueryValueEx( reg_handle, "ProxyEnable" )
        if proxy_enable:
            proxy_setting, reg_type = winreg.QueryValueEx( reg_handle, "ProxyServer" )
    finally:
        if reg_handle:
            reg_handle.Close()

    return proxy_setting
        

#--------------------------------------------------------------------

def adjustWindowPosition( new_window, pos ):

    window_rect = new_window.getWindowRect()
    char_w, char_h = new_window.getCharSize()
    offset = [ 0, 0 ]
           
    monitor_info_list = pyauto.Window.getMonitorInfo()
    for monitor_info in monitor_info_list:
        if monitor_info[0][0] <= pos[0] < monitor_info[0][2] and monitor_info[0][1] <= pos[1] < monitor_info[0][3]:
        
            if window_rect[0] < monitor_info[1][0]:
                offset[0] -= window_rect[0] - monitor_info[1][0]
            elif window_rect[2] > monitor_info[1][2]:
                offset[0] -= window_rect[2] - monitor_info[1][2]
        
            if window_rect[1] < monitor_info[1][1]:
                offset[1] -= window_rect[1] - monitor_info[1][1]
            elif window_rect[3] > monitor_info[1][3]:
                offset[1] -= window_rect[3] - monitor_info[1][3]
        
            break

    new_window.setPosSize( window_rect[0]+offset[0], window_rect[1]+offset[1], new_window.width(), new_window.height(), ORIGIN_X_LEFT | ORIGIN_Y_TOP )
