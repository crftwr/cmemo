#include <vector>
#include <list>
#include <string>

#include "windows.h"

#include "python.h"

#include "pythonutil.h"
#include "strutil.h"

#include "cmemo_native.h"

//using namespace cmemo;

//-----------------------------------------------------------------------------

#define MODULE_NAME "cmemo_native"
static PyObject * Error;

//-----------------------------------------------------------------------------

//#define PRINTF printf
//#define PRINTF PySys_WriteStdout
#define PRINTF(...)

//#define TRACE printf("%s(%d) : %s\n",__FILE__,__LINE__,__FUNCTION__)
//#define TRACE PySys_WriteStdout("%s(%d) : %s\n",__FILE__,__LINE__,__FUNCTION__)
#define TRACE

#if 0
	struct FuncTrace
	{
		FuncTrace( const char * _funcname, unsigned int _lineno )
		{
			funcname = _funcname;
			lineno   = _lineno;
		
			printf( "FuncTrace : Enter : %s(%)\n", funcname, lineno );
		}

		~FuncTrace()
		{
			printf( "FuncTrace : Leave : %s(%)\n", funcname, lineno );
		}
	
		const char * funcname;
		unsigned int lineno;
	};
	#define FUNC_TRACE FuncTrace functrace(__FUNCTION__,__LINE__)
#else
	#define FUNC_TRACE
#endif

// ----------------------------------------------------------------------------

class FindFileCache
{
public:
	FindFileCache( const std::wstring & _path, bool _ignore_dot, bool _ignore_dotdot, PyObject * _obj )
		:
		path(_path),
		ignore_dot(_ignore_dot),
		ignore_dotdot(_ignore_dotdot),
		obj(_obj)
	{
		Py_INCREF(obj);
	}

	FindFileCache( const FindFileCache & src )
		:
		path(src.path),
		ignore_dot(src.ignore_dot),
		ignore_dotdot(src.ignore_dotdot),
		obj(src.obj)
	{
		Py_INCREF(obj);
	}

	~FindFileCache()
	{
		Py_DECREF(obj);
	}

public:
	std::wstring path;
	bool ignore_dot;
	bool ignore_dotdot;
	PyObject * obj;
};

typedef std::list<FindFileCache> FindFileCacheList;
static FindFileCacheList find_file_cache_list;

static PyObject * _findFile(PyObject* self, PyObject* args, PyObject * kwds)
{
	PyObject * pypath;
	int ignore_dot = true;
	int ignore_dotdot = true;
	int use_cache = false;

    static char * kwlist[] = {
        "path",
        "ignore_dot",
        "ignore_dotdot",
        "use_cache",
        NULL
    };
    
    if(!PyArg_ParseTupleAndKeywords( args, kwds, "O|iii", kwlist,
        &pypath,
        &ignore_dot,
        &ignore_dotdot,
        &use_cache
    ))
    {
        return NULL;
	}

	std::wstring path;
	PythonUtil::PyStringToWideString( pypath, &path );
	
	PyObject * pyret = 0;
	
	if(use_cache)
	{
		// キャッシュを検索する
		FindFileCacheList::iterator i;
		for( i=find_file_cache_list.begin() ; i!=find_file_cache_list.end() ; ++i )
		{
			if( i->path == path
			 && i->ignore_dot == (ignore_dot!=0) 
			 && i->ignore_dotdot == (ignore_dotdot!=0) )
			{
				break;
			}
		}

		// キャッシュから見つかった		
		if(i!=find_file_cache_list.end())
		{
			pyret = i->obj;
			Py_INCREF(pyret);
		}
	}

	if(pyret==0)
	{
		WIN32_FIND_DATA data;

		pyret = PyList_New(0);
	
		HANDLE handle;

		Py_BEGIN_ALLOW_THREADS
		handle = FindFirstFile( path.c_str(), &data );
		Py_END_ALLOW_THREADS

		if(handle!=INVALID_HANDLE_VALUE)
		{
			while(true)
			{
				bool ignore = false;
		
				if( ignore_dot    && wcscmp(data.cFileName,L".")==0 ){ ignore = true; }
				if( ignore_dotdot && wcscmp(data.cFileName,L"..")==0 ){ ignore = true; }
		
				if(!ignore)
				{
					FILETIME local_file_time;
					SYSTEMTIME system_time;
		
					FileTimeToLocalFileTime( &data.ftLastWriteTime, &local_file_time );
					FileTimeToSystemTime( &local_file_time, &system_time );

					PyObject * pyitem = Py_BuildValue(
						"(uL(iiiiii)i)",
						data.cFileName,
						(((long long)data.nFileSizeHigh)<<32)+data.nFileSizeLow,
						system_time.wYear, system_time.wMonth, system_time.wDay,
						system_time.wHour, system_time.wMinute, system_time.wSecond,
						data.dwFileAttributes
					);
				
					PyList_Append( pyret, pyitem );

					Py_XDECREF(pyitem);
				}
		
				BOOL found;
				Py_BEGIN_ALLOW_THREADS
				found = FindNextFile(handle, &data);
				Py_END_ALLOW_THREADS
				if(!found) break;
			}

			Py_BEGIN_ALLOW_THREADS
			FindClose(handle);
			Py_END_ALLOW_THREADS
		}
		else if( GetLastError()==ERROR_FILE_NOT_FOUND )
		{
			// エラーにせず空のリストを返す
			SetLastError(0);
		}
		else
		{
			Py_XDECREF(pyret);
	
			PyErr_SetFromWindowsErr(0);
			return NULL;
		}
	}

	// キャッシュリストの先頭に登録する
	find_file_cache_list.push_front( FindFileCache( path, ignore_dot!=0, ignore_dotdot!=0, pyret ) );

	// キャッシュリストのサイズを４つに制限する
	while( find_file_cache_list.size()>4 )
	{
		find_file_cache_list.pop_back();
	}

	return pyret;
}

// ----------------------------------------------------------------------------

static PyObject * _setFileTime(PyObject* self, PyObject* args, PyObject * kwds)
{
	PyObject * pypath;
	int year, month, day, hour, minute, second;

    if( ! PyArg_ParseTuple( args, "O(iiiiii)", &pypath, &year, &month, &day, &hour, &minute, &second ) )
        return NULL;

	std::wstring path;
	PythonUtil::PyStringToWideString( pypath, &path );
	
	DWORD attr;
	Py_BEGIN_ALLOW_THREADS
	attr = GetFileAttributes(path.c_str());
	Py_END_ALLOW_THREADS
	if(attr==-1)
	{
		PyErr_SetString( PyExc_IOError, "could not get file attribute." );
		return NULL;
	}
	
    bool is_dir = (attr&FILE_ATTRIBUTE_DIRECTORY)!=0;
    bool is_readonly = (attr&FILE_ATTRIBUTE_READONLY)!=0;
    
    if(is_readonly)
    {
    	// ReadOnly 属性のときはいったん解除しないとタイムスタンプが更新できない
		Py_BEGIN_ALLOW_THREADS
		SetFileAttributes( path.c_str(), attr & (~FILE_ATTRIBUTE_READONLY) );
		Py_END_ALLOW_THREADS
    }
	
	HANDLE hFile;
	Py_BEGIN_ALLOW_THREADS
	hFile = CreateFile(
		path.c_str(), GENERIC_WRITE, 0, NULL,
		OPEN_EXISTING, is_dir?(FILE_ATTRIBUTE_NORMAL|FILE_FLAG_BACKUP_SEMANTICS):FILE_ATTRIBUTE_NORMAL, NULL
	);
	Py_END_ALLOW_THREADS

	if(hFile==INVALID_HANDLE_VALUE)
	{
		PyErr_SetString( PyExc_IOError, "could not open file." );

	    if(is_readonly)
	    {
	    	// ReadOnly 属性を元に戻す
			Py_BEGIN_ALLOW_THREADS
			SetFileAttributes( path.c_str(), attr );
			Py_END_ALLOW_THREADS
	    }

		return NULL;
	}

	SYSTEMTIME stFileTime;
	memset( &stFileTime, 0, sizeof(stFileTime) );
	stFileTime.wYear = year;
	stFileTime.wMonth = month;
	stFileTime.wDay = day;
	stFileTime.wHour = hour;
	stFileTime.wMinute = minute;
	stFileTime.wSecond = second;
	
	FILETIME ftFileTime;
	SystemTimeToFileTime(&stFileTime, &ftFileTime);

	FILETIME ftFileTimeUTC;
	LocalFileTimeToFileTime( &ftFileTime, &ftFileTimeUTC );

	Py_BEGIN_ALLOW_THREADS
	SetFileTime( hFile, NULL, NULL, &ftFileTimeUTC );
	Py_END_ALLOW_THREADS

	Py_BEGIN_ALLOW_THREADS
	CloseHandle(hFile);
	Py_END_ALLOW_THREADS

    if(is_readonly)
    {
    	// ReadOnly 属性を元に戻す
		Py_BEGIN_ALLOW_THREADS
		SetFileAttributes( path.c_str(), attr );
		Py_END_ALLOW_THREADS
    }

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * _chooseColor( PyObject * self, PyObject * args )
{
	HWND hwnd;
	int r, g, b;
	PyObject * py_color_table = NULL;

    if( ! PyArg_ParseTuple( args, "i(iii)O", &hwnd, &r, &g, &b, &py_color_table ) )
        return NULL;

	COLORREF initial_color = RGB(r,g,b);

	COLORREF color_table[16] = {0};
	if( PySequence_Check(py_color_table) )
	{
		int item_num = PySequence_Length(py_color_table);
		for( int i=0 ; i<item_num && i<16 ; i++ )
		{
			PyObject * item = PySequence_GetItem( py_color_table, i );

			if( PySequence_Check(item) )
			{
				if( PySequence_Length(item)==3 )
				{
					PyObject * obj_r = PySequence_GetItem( item, 0 );
					PyObject * obj_g = PySequence_GetItem( item, 1 );
					PyObject * obj_b = PySequence_GetItem( item, 2 );

					if( PyLong_Check(obj_r) &&
						PyLong_Check(obj_g) &&
						PyLong_Check(obj_b) )
					{
						color_table[i] = RGB( PyLong_AS_LONG(obj_r), PyLong_AS_LONG(obj_g), PyLong_AS_LONG(obj_b) );
					}
				}
			}
		}
	}

	CHOOSECOLOR cc = {0};

	cc.lStructSize	= sizeof(CHOOSECOLOR);
	cc.hwndOwner	= hwnd;
	cc.rgbResult	= initial_color;
	cc.lpCustColors	= color_table;
	cc.Flags = CC_FULLOPEN | CC_RGBINIT;

	BOOL result = ChooseColor(&cc);

	int color_table_rgb[16][3];
	for( int i=0 ; i<16 ; i++ )
	{
		color_table_rgb[i][0] = GetRValue(cc.lpCustColors[i]);
		color_table_rgb[i][1] = GetGValue(cc.lpCustColors[i]);
		color_table_rgb[i][2] = GetBValue(cc.lpCustColors[i]);
	}

	PyObject * pyret = Py_BuildValue( "i(iii)((iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii))",
		result,
		GetRValue(cc.rgbResult), GetGValue(cc.rgbResult), GetBValue(cc.rgbResult),
		color_table_rgb[ 0][0], color_table_rgb[ 0][1], color_table_rgb[ 0][2],
		color_table_rgb[ 1][0], color_table_rgb[ 1][1], color_table_rgb[ 1][2],
		color_table_rgb[ 2][0], color_table_rgb[ 2][1], color_table_rgb[ 2][2],
		color_table_rgb[ 3][0], color_table_rgb[ 3][1], color_table_rgb[ 3][2],
		color_table_rgb[ 4][0], color_table_rgb[ 4][1], color_table_rgb[ 4][2],
		color_table_rgb[ 5][0], color_table_rgb[ 5][1], color_table_rgb[ 5][2],
		color_table_rgb[ 6][0], color_table_rgb[ 6][1], color_table_rgb[ 6][2],
		color_table_rgb[ 7][0], color_table_rgb[ 7][1], color_table_rgb[ 7][2],
		color_table_rgb[ 8][0], color_table_rgb[ 8][1], color_table_rgb[ 8][2],
		color_table_rgb[ 9][0], color_table_rgb[ 9][1], color_table_rgb[ 9][2],
		color_table_rgb[10][0], color_table_rgb[10][1], color_table_rgb[10][2],
		color_table_rgb[11][0], color_table_rgb[11][1], color_table_rgb[11][2],
		color_table_rgb[12][0], color_table_rgb[12][1], color_table_rgb[12][2],
		color_table_rgb[13][0], color_table_rgb[13][1], color_table_rgb[13][2],
		color_table_rgb[14][0], color_table_rgb[14][1], color_table_rgb[14][2],
		color_table_rgb[15][0], color_table_rgb[15][1], color_table_rgb[15][2]
		);
	return pyret;
}

static PyMethodDef cmemo_native_funcs[] =
{
    { "findFile", (PyCFunction)_findFile, METH_VARARGS|METH_KEYWORDS, "" },
    { "setFileTime", (PyCFunction)_setFileTime, METH_VARARGS, "" },
    { "chooseColor", _chooseColor, METH_VARARGS, "" },
    {NULL, NULL, 0, NULL}
};

// ----------------------------------------------------------------------------

static PyModuleDef cmemo_native_module =
{
    PyModuleDef_HEAD_INIT,
    MODULE_NAME,
    "cmemo_native module.",
    -1,
    cmemo_native_funcs,
	NULL, NULL, NULL, NULL
};

extern "C" PyMODINIT_FUNC PyInit_cmemo_native(void)
{
    PyObject *m, *d;

    m = PyModule_Create(&cmemo_native_module);
    if(m == NULL) return NULL;

    d = PyModule_GetDict(m);

    Error = PyErr_NewException( MODULE_NAME".Error", NULL, NULL);
    PyDict_SetItemString( d, "Error", Error );

    if( PyErr_Occurred() )
    {
        Py_FatalError( "can't initialize module "MODULE_NAME );
    }

	return m;
}
