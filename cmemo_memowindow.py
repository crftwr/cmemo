import os
import time
import json
import traceback

from PIL import Image
import ckit
from ckit.ckit_const import *
import pyauto

import cmemo_native
import cmemo_ini
import cmemo_misc
import cmemo_resource

#--------------------------------------------------------------------

## メモウインドウ
#
class MemoWindow( ckit.TextWindow ):

    MODE_NORMAL = 0
    MODE_LINE = 1
    
    img_active = None

    def __init__( self, desktop, name, color ):
    
        self.initialized = False

        self.txt_filename = os.path.join( desktop.data_path, 'data', name+".txt" )
        self.cfg_filename = os.path.join( desktop.data_path, 'data', name+".cfg" )

        self.setting = { 
            "x":0, 
            "y":0, 
            "w":8, 
            "h":1, 
            "color":color, 
            "mode":MemoWindow.MODE_NORMAL 
            }
    
        try:
            fd = open( self.cfg_filename, "r", encoding="utf-8" )
            self.setting.update( json.load(fd) )
            fd.close()
            new_memo = False
        except:
            new_memo = True
    
        ckit.TextWindow.__init__(
            self,
            x=self.setting["x"],
            y=self.setting["y"],
            width=self.setting["w"],
            height=self.setting["h"],
            origin= ORIGIN_X_LEFT | ORIGIN_Y_TOP,
            show = False,
            resizable = False,
            title_bar = False,
            title = "",
            border_size = 2,
            minimizebox = False,
            maximizebox = False,
            tool = True,
            ncpaint = True,
            activate_handler = self._onActivate,
            close_handler = self.onClose,
            size_handler = self._onSize,
            keydown_handler = self.onKeyDown,
            lbuttondown_handler = self._onLeftButtonDown,
            rbuttondown_handler = self._onRightButtonDown,
            rbuttonup_handler = self._onRightButtonUp,
            lbuttondoubleclick_handler = self._onLeftButtonDoubleClick,
            nchittest_handler = self._onNcHitTest,
            )

        if new_memo:
            window_rect = self.getWindowRect()
            x, y = desktop.findSpace( ( window_rect[2]-window_rect[0]+4, window_rect[3]-window_rect[1]+4 ) )
            self.setPosSize(
                x=x+2,
                y=y+2,
                width=self.width(),
                height=self.height(),
                origin= ORIGIN_X_LEFT | ORIGIN_Y_TOP
                )

        self.command = ckit.CommandMap(self)

        self.desktop = desktop
        self.name = name
        
        self.txt_mtime = 0
        self.cfg_mtime = 0
        self.data = ""
        self.undo = None
        
        self.mode = self.setting["mode"]
        self.bg_color = self.setting["color"]

        self.configure()

        self.setTimer( self.onTimerCheckFile, 1000 )

        # アクティブ時の右下のしるし
        if not MemoWindow.img_active:
            MemoWindow.img_active = ckit.createThemeImage('active.png')

        self.plane_size = ( 13, 13 )
        self.plane_active = ckit.ImagePlane( self, (0,0), self.plane_size, 0 )
        self.plane_active.setImage(MemoWindow.img_active)
        self.plane_active.show(False)
        
        self.bell_count = 0;

        self.initialized = True

        self.saveSetting()

        self.load( adjust_size=new_memo )


    def destroy(self):

        self.plane_active.destroy()
        self.plane_active = None

        self.killTimer( self.onTimerCheckFile )

        ckit.TextWindow.destroy(self)

    ## 設定を読み込む
    #
    #  キーマップなどをリセットした上で、config,py の configure_MemoWindow() を呼び出します。
    #
    def configure(self):
        self.keymap = ckit.Keymap()
        self.keymap[ "Return" ] = self.command.Edit
        self.keymap[ "C-C" ] = self.command.SetClipboard
        self.keymap[ "C-V" ] = self.command.AppendFromClipboard
        self.keymap[ "C-Z" ] = self.command.Undo
        self.keymap[ "C-T" ] = self.command.ToggleLineMode
        self.keymap[ "Delete" ] = self.command.Delete
        ckit.callConfigFunc("configure_MemoWindow",self)

    def executeCommand( self, name, info ):

        try:
            command = getattr( self, "command_" + name )
        except AttributeError:
            return False
        
        command(info)
        return True

    def _onActivate( self, active ):
        if not self.initialized : return
        if self.plane_active:
            self.plane_active.show(active)

    def onClose(self):
        self.destroy()

    def _onSize( self, width, height ):
        self.paint()

    def _onLeftButtonDown( self, x, y, mod ):
        self.drag(x,y);
        
    def _onRightButtonDown( self, x, y, mod ):
        pass

    def _onRightButtonUp( self, x, y, mod ):

        menu_items = []
        
        menu_items.append( ( "編集(&E)", self.command_Edit ) )

        menu_items.append( ( "コピー(&C)", self.command_SetClipboard ) )

        menu_items.append( ( "貼り付け(&P)", self.command_AppendFromClipboard ) )

        menu_items.append( ( "-", None ) )

        menu_items.append( ( "色設定(&C)", self.command_SelectColor ) )

        menu_items.append( ( "１行表示(&T)", self.command_ToggleLineMode, bool(self.mode==MemoWindow.MODE_LINE) ) )

        menu_items.append( ( "-", None ) )

        menu_items.append( ( "削除(&D)", self.command_Delete ) )

        x, y = pyauto.Input.getCursorPos()
        self.popupMenu( x, y, menu_items )

    def _onLeftButtonDoubleClick( self, x, y, mod ):
        self.command.Edit()

    def onKeyDown( self, vk, mod ):

        try:
            func = self.keymap.table[ ckit.KeyEvent(vk,mod) ]
        except KeyError:
            return

        func()

        return True

    def _onNcHitTest( self, x, y ):

        pos = self.screenToClient(x,y)
        top_left = self.charToClient( 0, 0 )
        bottom_right = self.charToClient( self.width(), self.height() )
        
        if pos[0]<top_left[0]:
            if pos[1]<top_left[1]:
                return HTTOPLEFT
            elif pos[1]>bottom_right[1]:
                return HTBOTTOMLEFT
            else:
                return HTLEFT    
        elif pos[0]>=bottom_right[0]:
            if pos[1]<top_left[1]:
                return HTTOPRIGHT
            elif pos[1]>bottom_right[1]:
                return HTBOTTOMRIGHT
            else:
                return HTRIGHT
        else:
            if pos[1]<top_left[1]:
                return HTTOP
            elif pos[1]>bottom_right[1]:
                return HTBOTTOM
        
        return HTCLIENT

    def paint(self):

        x=0
        y=0
        width=self.width()
        height=self.height()

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()

        attribute_normal = ckit.Attribute( fg=self.fg_color )

        for i in range(height):
            if i < len(self.lines):
                self.putString( 0, y+i, width, 1, attribute_normal, " " * width )
                self.putString( 0, y+i, width, 1, attribute_normal, self.lines[i] )
            else:
                self.putString( 0, y+i, width, 1, attribute_normal, " " * width )

        self.plane_active.setPosition( ( client_rect[2]-13, client_rect[3]-13 ) )

    def load( self, adjust_size ):
    
        if self.data and self.undo!=self.data:
            self.undo = self.data
        
        try:
            self.txt_mtime = os.path.getmtime(self.txt_filename)
            fd = open( self.txt_filename, "rb" )
            self.data = fd.read()
            fd.close()
        except WindowsError as e:
            print( e )
            self.data = b""

        try:
            self.cfg_mtime = os.path.getmtime(self.cfg_filename)

            fd = open( self.cfg_filename, "r", encoding="utf-8" )
            self.setting.update( json.load(fd) )
            fd.close()

            self.mode = self.setting["mode"]
            self.bg_color = self.setting["color"]
        except (WindowsError,ValueError):
            self.mode = MemoWindow.MODE_NORMAL
            self.bg_color = self.desktop.default_memo_color

        self.encoding = ckit.detectTextEncoding( self.data, ascii_as="utf-8" )
        if self.encoding.bom:
            self.data = self.data[ len(self.encoding.bom) : ]

        if self.encoding.encoding==None:
            self.lines = []
        else:
            unicode_data = self.data.decode( self.encoding.encoding, 'replace' )
            self.lines = unicode_data.splitlines()

        if len(self.lines)>100:
            del self.lines[100:]
        
        for i in range(len(self.lines)):
            self.lines[i] = ckit.expandTab( self, self.lines[i] )
        
        width = self.width()
        height = self.height()
        
        if adjust_size:
            
            if self.mode==MemoWindow.MODE_NORMAL:
                # ノーマルモード
                max_line_width = 0
                for line in self.lines:
                    line_width = self.getStringWidth(line)
                    if max_line_width < line_width:
                        max_line_width = line_width
                width = min( max( max_line_width, 8 ), 80 )
                height = max( len(self.lines), 1 )
            
            elif self.mode==MemoWindow.MODE_LINE:
                # 1行モード
                line_width = 0
                if len(self.lines)>0:
                    line = self.lines[0]
                    line_width = self.getStringWidth(line)
                width = min( max( line_width, 8 ), 80 )
                height = 1
                

        window_rect = self.getWindowRect()
        align_right = False
        align_bottom = False
    
        # モニターの近いエッジとの距離を保ってサイズ変更する
        for monitor in pyauto.Window.getMonitorInfo():

            monitor_rect = monitor[1]
            
            if (window_rect[0]>=monitor_rect[0] and
                window_rect[1]>=monitor_rect[1] and
                window_rect[2]<=monitor_rect[2] and
                window_rect[3]<=monitor_rect[3] ):
               
                align_right = window_rect[0]-monitor_rect[0] > monitor_rect[2]-window_rect[2]
                align_bottom = window_rect[1]-monitor_rect[1] > monitor_rect[3]-window_rect[3]

                break

        origin = 0

        if align_right:
            x = window_rect[2]
            origin |= ORIGIN_X_RIGHT
        else:
            x = window_rect[0]
            origin |= ORIGIN_X_LEFT

        if align_bottom:
            y = window_rect[3]
            origin |= ORIGIN_Y_BOTTOM
        else:
            y = window_rect[1]
            origin |= ORIGIN_Y_TOP

        self.setColor(self.bg_color)
        
        self.setPosSize(
            x=x,
            y=y,
            width=width,
            height=height,
            origin = origin
            )

        self.show(True)

        self.paint()

    def saveSetting(self):

        rect = self.getWindowRect()

        new_setting = { 
            'x':rect[0], 
            'y':rect[1], 
            'w':self.width(), 
            'h':self.height(), 
            'color':self.bg_color, 
            "mode":self.mode
            }
            
        if self.setting != new_setting:

            fd = open( self.cfg_filename, "w", encoding="utf-8" )
            fd.write( json.dumps(new_setting) )
            fd.close()
            
            self.setting = new_setting

    def onTimerCheckFile(self):

        if not os.path.exists(self.txt_filename):
            self.desktop.deleteMemo(self.name)
            return

        try:
            txt_mtime = os.path.getmtime(self.txt_filename)
        except WindowsError:
            return

        try:
            cfg_mtime = os.path.getmtime(self.cfg_filename)
        except WindowsError:
            return

        if txt_mtime!=self.txt_mtime or cfg_mtime!=self.cfg_mtime:
            adjust_size = txt_mtime!=self.txt_mtime
            self.load( adjust_size=adjust_size )

    def setColor( self, color ):
    
        self.bg_color = color
        if color[0] + color[1] + color[2] >= 128 * 3:
            self.fg_color = ( 0, 0, 0 )
        else:    
            self.fg_color = ( 255, 255, 255 )
        self.frame_color = ( (self.bg_color[0]+self.fg_color[0])//2, (self.bg_color[1]+self.fg_color[1])//2, (self.bg_color[2]+self.fg_color[2])//2 )
        
        self.setBGColor(self.bg_color)
        self.setFrameColor(self.frame_color)

        self.paint()
        
    def getLeadingText( self, num_char ):
        s = ""
        for line in self.lines:
            line = line.strip()
            if len(line)==0 : continue
            s += line + " "
            if len(s) > num_char:
                break
        s = s[:num_char]
        return s
        
    def getTimeStamp(self):
        return self.txt_mtime

    def updateTimeStamp(self):
        cmemo_native.setFileTime( self.txt_filename, time.localtime()[0:6] )

    def getName(self):
        return self.name
        
    def _onTimerVisualBell(self):
        self.bell_count -= 1
        if self.bell_count>0:
            if self.bell_count % 2:
                self.setFrameColor( (255,255,255) )
            else:
                self.setFrameColor( (0,0,0) )
        else:
            self.setColor( self.bg_color )
            self.killTimer(self._onTimerVisualBell)

    def visualBell(self):
        self.bell_count = 8
        self.setTimer( self._onTimerVisualBell, 50 )

    #--------------------------------------------------------
    # ここから下のメソッドはキーに割り当てることができる
    #--------------------------------------------------------

    ## ファイルをエディタで編集する
    def command_Edit( self, info ):
        self.desktop.editTextFile(self.txt_filename)

    ## メモをクリップボードにコピーする
    def command_SetClipboard( self, info ):
        unicode_data = self.data.decode( self.encoding.encoding, 'replace' )
        ckit.setClipboardText( unicode_data )

    ## クリップボードの内容をメモの末尾に貼り付ける
    def command_AppendFromClipboard( self, info ):

        s = ckit.getClipboardText()
        s = s.replace("\r\n","\n")
        new_lines = self.lines + s.splitlines()
        s = "\r\n".join(new_lines)
        s = s.encode(self.encoding.encoding)
        
        fd = open( self.txt_filename, "wb" )
        fd.write(s)
        fd.close()
        
        self.load( adjust_size=True )

    ## 最後の変更を取り消す
    def command_Undo( self, info ):
    
        if self.undo==None : return
            
        fd = open( self.txt_filename, "wb" )
        fd.write(self.undo)
        fd.close()
        
        self.load( adjust_size=True )

    ## このメモを削除する    
    def command_Delete( self, info ):
        self.desktop.deleteMemo(self.name)

    ## 色を設定する
    def command_SelectColor( self, info ):
        result, color, self.desktop.color_choose_table = cmemo_native.chooseColor( self.getHWND(), self.bg_color, self.desktop.color_choose_table )
        if not result: return
        self.setColor(color)
        self.saveSetting()
        self.load( adjust_size=False )

    ## １行表示モードとノーマルモードを切り替える
    def command_ToggleLineMode( self, info ):
        if self.mode!=MemoWindow.MODE_LINE:
            self.mode = MemoWindow.MODE_LINE
        else:    
            self.mode = MemoWindow.MODE_NORMAL
        self.saveSetting()
        self.load( adjust_size=True )

