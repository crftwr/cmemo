
cmemo_appname = "CraftMemo"
cmemo_dirname = "CraftMemo"
cmemo_version = "1.28"

_startup_string_fmt = """\
%s version %s:
  http://sites.google.com/site/craftware/
"""

def startupString():
    return _startup_string_fmt % ( cmemo_appname, cmemo_version )
