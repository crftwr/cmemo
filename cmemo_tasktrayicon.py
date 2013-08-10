import os
import sys
import webbrowser

import ckit
import pyauto

import cmemo_misc

class TaskTrayIcon( ckit.TaskTrayIcon ):
    
    def __init__( self, console_window, desktop ):
    
        ckit.TaskTrayIcon.__init__( self,
            title = "CraftMemo",
            lbuttondown_handler = self._onLeftButtonDown,
            lbuttonup_handler = self._onLeftButtonUp,
            rbuttondown_handler = self._onRightButtonDown,
            rbuttonup_handler = self._onRightButtonUp,
            lbuttondoubleclick_handler = self._onLeftButtonDoubleClick,
            )
        
        self.console_window = console_window
        self.desktop = desktop

    def _onLeftButtonDown( self, x, y, mod ):
        pass

    def _onLeftButtonUp( self, x, y, mod ):
        self.console_window.show(True,True)
        self.console_window.restore()
        self.console_window.foreground()

    def _onRightButtonDown( self, x, y, mod ):
        pass

    def _onRightButtonUp( self, x, y, mod ):

        def onReloadConfig(info):
            self.desktop.configure()
            print( "設定をリロードしました" )
            print( "" )

        def onEditConfig(info):

            def jobHelp(job_item):
                self.desktop.editConfigFile()

            def jobHelpFinished(job_item):
                print( "設定ファイルのエディタを起動しました" )
                print( "" )
            
            job_item = ckit.JobItem( jobHelp, jobHelpFinished )
            ckit.JobQueue.defaultQueue().enqueue(job_item)

        def onClearConsole(info):
            self.console_window.clearLog()

        def onHelp(info):
        
            def jobHelp(job_item):
                help_path = os.path.join( ckit.getAppExePath(), 'doc\\index.html' )
                pyauto.shellExecute( None, help_path, "", "" )

            def jobHelpFinished(job_item):
                print( "Helpを開きました" )
                print( "" )
            
            job_item = ckit.JobItem( jobHelp, jobHelpFinished )
            ckit.JobQueue.defaultQueue().enqueue(job_item)
        
        def onExit(info):
            self.desktop.quit()
        
        menu_items = []
        
        menu_items.append( ( "新規作成(&N)", self.desktop.command_NewMemo ) )

        menu_items.append( ( "貼り付け(&V)", self.desktop.command_NewMemoFromClipboard ) )

        menu_items.append( ( "-", None ) )

        menu_items.append( ( "非表示(&H)", self.desktop.command_ToggleHide, not self.desktop.isAllVisible() ) )

        menu_items.append( ( "リスト(&L)", self.desktop.command_List ) )

        menu_items.append( ( "-", None ) )

        menu_items.append( ( "設定のリロード(&R)", onReloadConfig ) )

        menu_items.append( ( "設定の編集(&E)", onEditConfig ) )
        
        menu_items.append( ( "端末のクリア(&C)", onClearConsole ) )
            
        menu_items.append( ( "-", None ) )

        menu_items.append( ( "ヘルプ(&H)", onHelp ) )

        menu_items.append( ( "-", None ) )

        menu_items.append( ( "CraftMemoの終了(&X)", onExit ) )

        x, y = pyauto.Input.getCursorPos()
        self.popupMenu( x, y, menu_items )

    def _onLeftButtonDoubleClick( self, x, y, mod ):
        #print( "_onLeftButtonDoubleClick", x, y, mod )
        pass

