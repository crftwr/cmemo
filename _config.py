import os

from cmemo import *

def configure(desktop):

    # config.py編集用のテキストエディタの設定
    desktop.editor = "notepad.exe"

    # メニューを出すためのホットキーの設定
    desktop.setMenuHotKey( ord('P'), MODKEY_CTRL|MODKEY_SHIFT )
    
    # デフォルトのメモウインドウの色の設定
    desktop.default_memo_color = ( 255, 255, 128 )

    # データ置き場
    # DropBox による同期を活用する例
    #desktop.data_path = os.path.join( getProfilePath(), "Dropbox/cmemo" )


def configure_MemoWindow(window):
    
    #print( "configure_MemoWindow", window )
    pass
