import os
import sys
import msvcrt
import configparser

import ckit

import cmemo_resource

ini = None
ini_filename = os.path.join( ckit.getAppExePath(), 'cmemo.ini' )
dirty = False

#--------------------------------------------------------------------

def read():

    global ini
    global dirty

    ini = configparser.RawConfigParser()

    try:
        fd = open( ini_filename, "r", encoding="utf-8" )
        msvcrt.locking( fd.fileno(), msvcrt.LK_LOCK, 1 )
        ini.readfp(fd)
        fd.close()
    except:
        pass
    dirty = False

def write( check_dirty=True ):
    global dirty
    if check_dirty and not dirty: return
    try:
        fd = open( ini_filename, "w", encoding="utf-8" )
        msvcrt.locking( fd.fileno(), msvcrt.LK_LOCK, 1 )
        ini.write(fd)
        fd.close()
    except:
        pass
    dirty = False

def get( section, option, default=None ):
    try:
        return ini.get( section, option )
    except:
        if default!=None:
            return default
        raise

def getint( section, option, default=None ):
    try:
        return ini.getint( section, option )
    except:
        if default!=None:
            return default
        raise

def set( section, option, value ):

    global dirty
    assert( type(value)==str )

    try:
        ini.add_section(section)
        dirty=True
    except configparser.DuplicateSectionError:
        pass
    
    try:    
        if ini.get(section, option)==value:
            return
    except:
        pass

    ini.set( section, option, value )
    dirty=True

def setint( section, option, value ):
    global dirty
    assert( type(value)==int )
    set( section, option, str(value) )

def remove_section(section):
    global dirty
    result = ini.remove_section(section)
    dirty=True
    return result

def remove_option( section, option ):
    global dirty
    result = ini.remove_option( section, option )
    dirty=True
    return result
