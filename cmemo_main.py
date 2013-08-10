import sys
import os
import getopt
import shutil

os.environ["PATH"] = os.path.join( os.path.split(sys.argv[0])[0], 'lib' ) + ";" + os.environ["PATH"]

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    os.path.join( os.path.split(sys.argv[0])[0], 'extension' ),
    os.path.join( os.path.split(sys.argv[0])[0], 'lib' ),
    ]

import ckit

import cmemo_desktop
import cmemo_ini
import cmemo_misc
import cmemo_resource

#--------------------------------------------------------------------

debug = False
profile = False

option_list, args = getopt.getopt( sys.argv[1:], "dp" )
for option in option_list:
    if option[0]=="-d":
        debug = True
    elif option[0]=="-p":
        profile = True

#--------------------------------------------------------------------

if __name__ == "__main__":

    ckit.registerWindowClass( "Cmemo" )
    
    sys.path[0:0] = [
        os.path.join( ckit.getAppExePath(), 'extension' ),
        os.path.join( ckit.getAppExePath(), 'script' ),
        ]

    # exeと同じ位置にある設定ファイルを優先する
    if os.path.exists( os.path.join( ckit.getAppExePath(), 'config.py' ) ):
        ckit.setDataPath( ckit.getAppExePath() )
    else:    
        ckit.setDataPath( os.path.join( ckit.getAppDataPath(), cmemo_resource.cmemo_dirname ) )
        if not os.path.exists(ckit.dataPath()):
            os.mkdir(ckit.dataPath())

    default_config_filename = os.path.join( ckit.getAppExePath(), '_config.py' )
    config_filename = os.path.join( ckit.dataPath(), 'config.py' )
    cmemo_ini.ini_filename = os.path.join( ckit.dataPath(), 'cmemo.ini' )

    # config.py がどこにもない場合は作成する
    if not os.path.exists(config_filename) and os.path.exists(default_config_filename):
        shutil.copy( default_config_filename, config_filename )
    
    cmemo_ini.read()

    ckit.JobQueue.createDefaultQueue()

    desktop = cmemo_desktop.Desktop( config_filename, debug, profile )
        
    desktop.configure()
    
    desktop.startup()
    
    desktop.messageLoop()

    desktop.saveState()

    desktop.destroy()

    cmemo_ini.write()    

