import json
import cmemo_ini

class ColorSetting:

    def __init__( self, color, enabled, next=None ):
        self.color = color
        self.enabled = enabled
        self.next = next

    def getColor(self):
        if self.enabled:
            return self.color
        elif self.next:
            return self.next.getColor()
        else:
            return (0,0,0)

def loadSetting():

    global bg_setting
    global fg_setting
    global bar_fg_setting
    global bar_error_fg_setting
    global select_bg_setting
    global choice_bg_setting
    global edit_fg_setting
    global edit_select_fg_setting
    global edit_select_bg_setting
    global candlist_fg_setting
    global candlist_bg_setting
    global candlist_select_fg_setting
    global candlist_select_bg_setting
    
    def createColorSetting( name, default ):
        color = json.loads( cmemo_ini.get( "COLOR", name, default ) )
        return ColorSetting( tuple(color), True )

    bg_setting                  = createColorSetting( "bg",                "[   0,   0,   0 ]" )
    fg_setting                  = createColorSetting( "fg",                "[ 255, 255, 255 ]" )
    bar_fg_setting              = createColorSetting( "bar_fg",            "[   0,   0,   0 ]" )
    bar_error_fg_setting        = createColorSetting( "bar_error_fg",      "[ 200,   0,   0 ]" )
    select_bg_setting           = createColorSetting( "select_bg",         "[  30, 100, 150 ]" )
    choice_bg_setting           = createColorSetting( "choice_bg",         "[  50,  50,  50 ]" )
    edit_fg_setting             = createColorSetting( "edit_fg",           "[ 255, 255, 255 ]" )
    edit_select_fg_setting      = createColorSetting( "edit_select_fg",    "[ 255, 255, 255 ]" )
    edit_select_bg_setting      = createColorSetting( "edit_select_bg",    "[  30, 100, 150 ]" )
    candlist_fg_setting         = createColorSetting( "candlist_fg",       "[ 255, 255, 255 ]" )
    candlist_bg_setting         = createColorSetting( "candlist_bg",       "[  16,  26,  56 ]" )
    candlist_select_fg_setting  = createColorSetting( "candlist_select_fg","[ 255, 255, 255 ]" )
    candlist_select_bg_setting  = createColorSetting( "candlist_select_bg","[  30, 100, 150 ]" )

    _applySetting()

def saveSetting():
    
    _applySetting()
    
    cmemo_ini.set( "COLOR", "bg",                   json.dumps( bg_setting.color ) )
    cmemo_ini.set( "COLOR", "fg",                   json.dumps( fg_setting.color ) )
    cmemo_ini.set( "COLOR", "bar_fg",               json.dumps( bar_fg_setting.color ) )
    cmemo_ini.set( "COLOR", "bar_error_fg",         json.dumps( bar_error_fg_setting.color ) )
    cmemo_ini.set( "COLOR", "select_bg",            json.dumps( select_bg_setting.color ) )
    cmemo_ini.set( "COLOR", "choice_bg",            json.dumps( choice_bg_setting.color ) )
    cmemo_ini.set( "COLOR", "edit_fg",              json.dumps( edit_fg_setting.color ) )
    cmemo_ini.set( "COLOR", "edit_select_fg",       json.dumps( edit_select_fg_setting.color ) )
    cmemo_ini.set( "COLOR", "edit_select_bg",       json.dumps( edit_select_bg_setting.color ) )
    cmemo_ini.set( "COLOR", "candlist_fg",          json.dumps( candlist_fg_setting.color ) )
    cmemo_ini.set( "COLOR", "candlist_bg",          json.dumps( candlist_bg_setting.color ) )
    cmemo_ini.set( "COLOR", "candlist_select_fg",   json.dumps( candlist_select_fg_setting.color ) )
    cmemo_ini.set( "COLOR", "candlist_select_bg",   json.dumps( candlist_select_bg_setting.color ) )
   

def _applySetting():
    
    global bg
    global fg
    global bar_fg
    global bar_error_fg
    global select_bg
    global choice_bg
    global edit_fg
    global edit_select_fg
    global edit_select_bg
    global candlist_fg
    global candlist_bg
    global candlist_select_fg
    global candlist_select_bg

    bg                  = bg_setting.getColor()
    fg                  = fg_setting.getColor()
    bar_fg              = bar_fg_setting.getColor()
    bar_error_fg        = bar_error_fg_setting.getColor()
    select_bg           = select_bg_setting.getColor()
    choice_bg           = choice_bg_setting.getColor()
    edit_fg             = edit_fg_setting.getColor()
    edit_select_fg      = edit_select_fg_setting.getColor()
    edit_select_bg      = edit_select_bg_setting.getColor()
    candlist_fg         = candlist_fg_setting.getColor()
    candlist_bg         = candlist_bg_setting.getColor()
    candlist_select_fg  = candlist_select_fg_setting.getColor()
    candlist_select_bg  = candlist_select_bg_setting.getColor()
