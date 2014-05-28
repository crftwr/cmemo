import os
import sys
import profile
import uuid
import json
import threading
import traceback

import ckit
from ckit.ckit_const import *
import pyauto

import cmemo_memowindow
import cmemo_listwindow
import cmemo_consolewindow
import cmemo_tasktrayicon
import cmemo_ini
import cmemo_resource
import cmemo_colortable
import cmemo_misc

## @addtogroup desktop
## @{

#--------------------------------------------------------------------

## 複数のメモウインドウの管理を行うクラス
#
class Desktop(ckit.TextWindow):
    
    def __init__( self, config_filename, debug, profile ):

        ckit.TextWindow.__init__(
            self,
            x = 0,
            y = 0,
            width = 1,
            height = 1,
            title_bar = True,
            title = "cmemo manager",
            show = False,
            sysmenu=True,
            endsession_handler = self._onEndSession,
            )
        
        self.command = ckit.CommandMap(self)

        self.config_filename = config_filename  # config.py のファイルパス
        self.editor = ""                        # config.pyを編集するためのテキストエディタ
        self.data_path = ckit.dataPath()        # メモデータ置き場
        self.debug = debug                      # デバッグモード
        self.profile = profile                  # プロファイルモード
        
        self.memowindow_table = {}
    
        self.color_choose_table = ( (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0) )
        self.default_memo_color = (255,255,192)
        
        self.loadState()

        self.user_input_ownership = threading.Lock()
        self.user_input_other_acquire_handler = None
        
        self.setTimer( self._onTimerCheckFileAll, 3*1000 )
        self.setTimer( self._onTimerFlushIniFile, 10*1000 )

        self.console_window = cmemo_consolewindow.ConsoleWindow( self, debug )

        self.task_tray_icon = cmemo_tasktrayicon.TaskTrayIcon( self.console_window, self )
    
        self.console_window.registerStdio()

    def destroy(self):

        self.console_window.unregisterStdio()

        for memowindow in self.memowindow_table.values():
            memowindow.destroy()

        self.task_tray_icon.destroy()

        self.console_window.destroy()

        ckit.TextWindow.destroy(self)

    def _onEndSession(self):
        self.saveState()
        cmemo_ini.write()

    def enableDebug( self, enable ):
        self.debug = enable

    ## ユーザ入力権を獲得する
    #
    #  @param self      -
    #  @param blocking  ユーザ入力権を獲得するまでブロックするか
    #  @param other_acquire_handler 入力権を所有中に再度入力権を獲得しようとしたときに呼ばれるハンドラ
    #
    #  マウスやキーボードで操作させる権利を獲得するための関数です。\n\n
    #
    #  バックグラウンド処理の途中や最後でユーザの操作を受け付ける場合には、
    #  releaseUserInputOwnership と releaseUserInputOwnership を使って、
    #  入力権を所有する必要があります。
    #  さもないと、フォアグラウンドのユーザ操作と衝突してしまい、ユーザが混乱したり、
    #  正しく動作しなくなります。\n\n
    #
    #  @sa releaseUserInputOwnership
    #
    def acquireUserInputOwnership( self, blocking=1, other_acquire_handler=None ):
        result = self.user_input_ownership.acquire(blocking)
        if result:
            self.user_input_other_acquire_handler = other_acquire_handler
        else:
            if self.user_input_other_acquire_handler : self.user_input_other_acquire_handler()    
        return result
    
    ## ユーザ入力権を解放する
    #
    #  @sa acquireUserInputOwnership
    #
    def releaseUserInputOwnership(self):
        self.user_input_ownership.release()
        self.user_input_other_acquire_handler = None

    ## 設定を読み込む
    def configure(self):
    
        ckit.Keymap.init()

        self.editor = "notepad.exe"
        self.data_path = ckit.dataPath()

        ckit.reloadConfigScript( self.config_filename )
        ckit.callConfigFunc("configure",self)
        
    def executeCommand( self, name, info ):

        try:
            command = getattr( self, "command_" + name )
        except AttributeError:
            return False
        
        command(info)
        return True

    def editConfigFile(self):
        
        fullpath = os.path.abspath(self.config_filename)
    
        if callable(self.editor):
            self.editor(fullpath)
        else:
            pyauto.shellExecute( None, self.editor, '"%s"' % fullpath, "" )

    def startup(self):

        print( cmemo_resource.startupString() )

        # データ置き場を作成する
        dirname_list = [
            self.data_path,
            os.path.join( self.data_path, 'data' ),
            os.path.join( self.data_path, 'backup' ),
        ]
        for dirname in dirname_list:
            if dirname:
                if not os.path.exists(dirname):
                    os.mkdir(dirname)

        self.loadMemos()

    def newMemo( self, data, edit=False ):

        # ユニークなID
        name = "memo_" + uuid.uuid1().hex[:8]

        # utf-8 / CR-LF に変換
        utf8_bom = b"\xEF\xBB\xBF"
        data = data.replace("\r\n","\n")
        data = data.replace("\r","\n")
        data = data.replace("\n","\r\n")
        data = data.encode( encoding="utf-8" )

        # ファイルの新規作成
        data_path = os.path.join( self.data_path, 'data' )
        fullpath = os.path.join( data_path, name+".txt" )
        fd = open( fullpath, "wb" )
        fd.write(utf8_bom)
        fd.write(data)
        fd.close()
        
        # テキストエディタを開く
        if edit:
            self.editTextFile(fullpath)
                
        new_memowindow = cmemo_memowindow.MemoWindow( self, name, self.default_memo_color )
        self.memowindow_table[name] = new_memowindow
    
    def deleteMemo(self,name):
        
        # ウインドウの削除
        memowindow = self.memowindow_table[name]
        memowindow.destroy()
        del self.memowindow_table[name]
        
        # データファイルの移動/削除
        data_path = os.path.join( self.data_path, 'data' )
        backup_path = os.path.join( self.data_path, 'backup' )
        txt_fullpath = os.path.join( data_path, name+".txt" )
        cfg_fullpath = os.path.join( data_path, name+".cfg" )
        bak_fullpath = os.path.join( backup_path, name+".txt" )

        # 既にバックアップが存在していたら削除する。
        # テキストエディタで開いたまま、メモを削除し、テキストエディタから保存した場合に、
        # ２重に削除されるケースがありえる。
        if os.path.exists(bak_fullpath):
            os.unlink(bak_fullpath)

        if os.path.exists(txt_fullpath):
            os.rename( txt_fullpath, bak_fullpath )
        if os.path.exists(cfg_fullpath):
            os.unlink(cfg_fullpath)
    
    def loadMemos(self):
        data_path = os.path.join( self.data_path, 'data' )
        filename_list = os.listdir(data_path)
        for filename in filename_list:
            name, ext = os.path.splitext(filename)
            if ext.lower()==".txt":
                new_memowindow = cmemo_memowindow.MemoWindow( self, name, self.default_memo_color )
                self.memowindow_table[name] = new_memowindow

    def findSpace( self, size ):
    
        for monitor in pyauto.Window.getMonitorInfo():

            monitor_rect = monitor[1]
            
            for x in range( monitor_rect[0], monitor_rect[2]-size[0], size[0] ):
                for y in range( monitor_rect[1], monitor_rect[3]-size[1], size[1] ):
                    
                    hit = False
                    
                    for memowindow in self.memowindow_table.values():
                        memowindow_rect = memowindow.getWindowRect()
                        if (x>=memowindow_rect[2] or x+size[0]<=memowindow_rect[0] or
                            y>=memowindow_rect[3] or y+size[1]<=memowindow_rect[1] ):
                            pass
                        else:
                            hit = True
                            break
                    
                    if not hit:
                        return x, y

        return [ 20, 20 ]

    def editTextFile(self,filename):

        filename = os.path.abspath(filename)

        if callable(self.editor):
            self.editor(filename)
        else:
            pyauto.shellExecute( None, self.editor, '"%s"' % filename, "" )
            
    def _popupHotKeyMenu(self):
        
        if not self.acquireUserInputOwnership(False) : return
        try:
            menu_items = []
        
            menu_items.append( ( "新規作成(&N)", self.command_NewMemo ) )

            menu_items.append( ( "貼り付け(&V)", self.command_NewMemoFromClipboard ) )

            menu_items.append( ( "-", None ) )

            menu_items.append( ( "非表示(&H)", self.command_ToggleHide, not self.isAllVisible() ) )

            if len(self.memowindow_table):

                menu_items.append( ( "リスト(&L)", self.command_List ) )

            x, y = pyauto.Input.getCursorPos()
            self.popupMenu( x, y, menu_items )

        finally:
            self.releaseUserInputOwnership()

    def setMenuHotKey( self, vk, mod ):
        self.killHotKey( self._popupHotKeyMenu )
        ckit.TextWindow.setHotKey( self, vk, mod, self._popupHotKeyMenu )

    def _onTimerCheckFileAll(self):
        data_path = os.path.join( self.data_path, 'data' )
        filename_list = os.listdir(data_path)
        for filename in filename_list:
            name, ext = os.path.splitext(filename)
            if ext.lower()==".txt":
                if name in self.memowindow_table:
                    pass
                else:
                    new_memowindow = cmemo_memowindow.MemoWindow( self, name, self.default_memo_color )
                    self.memowindow_table[name] = new_memowindow

    def _onTimerFlushIniFile(self):
        self.saveState()
        cmemo_ini.write()

    def isAllVisible(self):
        for memowindow in self.memowindow_table.values():
            if not memowindow.isVisible() : return False
        return True    

    #--------------------------------------------------------------------------
    # 状態の保存と復帰

    def loadState(self):
        cmemo_colortable.loadSetting()
        try:
            self.color_choose_table = json.loads( cmemo_ini.get( "MISC", "color_choose_table" ) )
        except:
            pass

    def saveState(self):
        self.console_window.saveState()
        cmemo_ini.set( "MISC", "color_choose_table", json.dumps(self.color_choose_table) )
        for memowindow in self.memowindow_table.values():
            memowindow.saveSetting()
        

    #--------------------------------------------------------
    # ここから下のメソッドはキーに割り当てることができる
    #--------------------------------------------------------

    def command_NewMemo( self, info ):
        self.newMemo( data="", edit=True )

    def command_NewMemoFromClipboard( self, info ):
        s = ckit.getClipboardText()
        self.newMemo( data=s, edit=False )
        
    def command_ToggleHide( self, info ):
        visible = not self.isAllVisible()
        for memowindow in self.memowindow_table.values():
            memowindow.show(visible)
    
    def command_List( self, info ):

        def activatePopup():
            list_window.foreground()

        if not self.acquireUserInputOwnership(False,activatePopup) : return
        try:
            items = list( self.memowindow_table.values() )
        
            if len(items)==0:
                return

            items.sort( key = lambda item : item.getTimeStamp(), reverse=True )

            def build_item(memowindow):
                return ( memowindow.getLeadingText(1000), memowindow )
            items = list(map( build_item, items ))

            initial_select = 0
            max_width = 60

            def onKeyDown( vk, mod ):
                pass

            def onStatusMessage( width, select ):
                return ""

            pos = pyauto.Input.getCursorPos()
            list_window = cmemo_listwindow.ListWindow( pos[0], pos[1], 5, 1, max_width, 16, 0, False, "メモリスト", items, initial_select=0, keydown_hook=onKeyDown, onekey_search=False, statusbar_handler=onStatusMessage )
            cmemo_misc.adjustWindowPosition( list_window, pos )
            list_window.show(True)
            self.enable(False)
            list_window.messageLoop()
            result = list_window.getResult()
            self.enable(True)
            self.activate()
            list_window.destroy()

            if result<0 : return

            items[result][1].updateTimeStamp()
            items[result][1].activate()
            items[result][1].visualBell()
        
        finally:
            self.releaseUserInputOwnership()

## @} desktop

