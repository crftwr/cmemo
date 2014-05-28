import os
import sys
import subprocess
import shutil
import zipfile
import hashlib

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    ]

import cmemo_resource

DIST_DIR = "dist/cmemo"
DIST_SRC_DIR = "dist/src"
VERSION = cmemo_resource.cmemo_version.replace(".","").replace(" ","")
ARCHIVE_NAME = "cmemo_%s.zip" % VERSION

PYTHON_DIR = "c:/python34"
PYTHON = PYTHON_DIR + "/python.exe"
SVN_DIR = "c:/Program Files/TortoiseSVN/bin"
DOXYGEN_DIR = "c:/Program Files/doxygen"

def unlink(filename):
    try:
        os.unlink(filename)
    except OSError:
        pass

def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError:
        pass

def rmtree(dirname):
    try:
        shutil.rmtree(dirname)
    except OSError:
        pass

def createZip( zip_filename, items ):
    z = zipfile.ZipFile( zip_filename, "w", zipfile.ZIP_DEFLATED, True )
    for item in items:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                for f in files:
                    f = os.path.join(root,f)
                    print( f )
                    z.write(f)
        else:
            print( item )
            z.write(item)
    z.close()

DIST_FILES = [
    "cmemo/cmemo.exe",
    "cmemo/lib",
    "cmemo/python34.dll",
    "cmemo/library.zip",
    "cmemo/_config.py",
    "cmemo/readme.txt",
    "cmemo/theme/black",
    "cmemo/license",
    "cmemo/doc",
    "cmemo/dict/.keepme",
    "cmemo/extension/.keepme",
    ]

def all():
    doc()
    exe()

def exe():
    subprocess.call( [ PYTHON, "setup.py", "build" ] )

    if 0:
        rmtree( DIST_SRC_DIR )
        makedirs( DIST_SRC_DIR )
        os.chdir(DIST_SRC_DIR)
        subprocess.call( [ SVN_DIR + "/svn.exe", "export", "--force", "../../../ckit" ] )
        subprocess.call( [ SVN_DIR + "/svn.exe", "export", "--force", "../../../pyauto" ] )
        subprocess.call( [ SVN_DIR + "/svn.exe", "export", "--force", "../../../cmemo" ] )
        os.chdir("..")
        createZip( "cmemo/src.zip", [ "src" ] )
        os.chdir("..")

    if 1:
        os.chdir("dist")
        createZip( ARCHIVE_NAME, DIST_FILES )
        os.chdir("..")
    
    fd = open( "dist/%s" % ARCHIVE_NAME, "rb" )
    m = hashlib.md5()
    while 1:
        data = fd.read( 1024 * 1024 )
        if not data: break
        m.update(data)
    fd.close()
    print( "" )
    print( m.hexdigest() )

def clean():
    rmtree("dist")
    rmtree("build")
    rmtree("doc/html")
    unlink( "tags" )

def doc():
    rmtree( "doc/html" )
    makedirs( "doc/obj" )
    makedirs( "doc/html" )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/index.txt", "doc/obj/index.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/index.txt", "doc/obj/index.htm_" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/changes.txt", "doc/obj/changes.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/changes.txt", "doc/obj/changes.htm_" ] )
    subprocess.call( [ DOXYGEN_DIR + "/bin/doxygen.exe", "doc/doxyfile" ] )
    shutil.copytree( "doc/image", "doc/html/image", ignore=shutil.ignore_patterns(".svn","*.pdn") )

def run():
    subprocess.call( [ PYTHON, "cmemo_main.py" ] )

def debug():
    subprocess.call( [ PYTHON, "cmemo_main.py", "-d" ] )

def profile():
    subprocess.call( [ PYTHON, "cmemo_main.py", "-d", "-p" ] )

if len(sys.argv)<=1:
    target = "all"
else:
    target = sys.argv[1]

eval( target + "()" )

