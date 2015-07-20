
cmemo_appname = "CraftMemo"
cmemo_dirname = "CraftMemo"
cmemo_version = "1.24 debug 1"

_startup_string_fmt = """\
%s version %s:
  http://sites.google.com/site/craftware/
"""

def startupString():
    return _startup_string_fmt % ( cmemo_appname, cmemo_version )
