#!/usr/bin/python3
# setup.py
from setuptools import setup
import sys
import glob
import os.path
if sys.version_info >= (3,0,0):
    basestring = str
from easyabc_version import program_version, program_name

long_description = f"Nils Liberg's {program_name}"
url = 'https://sourceforge.net/projects/easyabc/'
author = 'Nils Liberg, Jan Wybren de Wong, Seymour Shlien, Frederic Aupepin'

options = {}
executables = []

include_files = [os.path.join('locale', 'sv', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'sv', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'da', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'da', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'de', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'de', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'fr', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'fr', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'nl', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'nl', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'ja', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'ja', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'it', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'it', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'zh_CN', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'zh_CN', 'LC_MESSAGES', 'easyabc.mo')] + \
                 glob.glob(os.path.join('img', '*.*')) + glob.glob(os.path.join('sound', '*.*')) + \
                 glob.glob(os.path.join('docs', '*.*')) + \
                 glob.glob(os.path.join('docs', 'en', '*.*')) + \
                 glob.glob(os.path.join('docs', 'fr', '*.*'))

if sys.platform == "darwin":
    import py2app
#    import bdist_mpkg
    buildstyle = 'app'
    options["py2app"] = {"argv_emulation" : False,
                         'iconfile'       : "img/EasyABC.icns",
                         "resources": ["img/ABCFile.icns"],
        #                 'optimize'       : 1,  #2
                         'compressed'     : True,
        #                 'excludes': ['Tkinter','tcl','tk','_ssl', 'email'],
                         'excludes': ['Tkinter','tcl','tk','_ssl', 'pygame', 'pygame.pypm'],
        #                 'includes': ['mechanize', 'urllib', 'socket', 'pygame.pypm' ],
                         'includes': ['urllib', 'socket' ],
                         'packages': ['wx'],
                         'plist': {
                                   'CFBundleDocumentTypes': [{
                                                              'CFBundleTypeExtensions': ['abc'],
                                                              'CFBundleTypeName': 'ABC notation file',
                                                              'CFBundleTypeRole': 'Editor',
                                                              'CFBundleTypeIconFile': 'ABCFile.icns',
                                                            }]
                                   }
                         }
    data_files = [('.', ['reference.txt', 'gpl-license.txt']),
                  #('bin', ['bin/abc2midi', 'bin/abcm2ps', 'bin/abc2abc', 'bin/nwc2xml', 'bin/midi2abc']),
                  ('img', glob.glob(os.path.join('img', '*.*'))),
                  ('sound', glob.glob(os.path.join('sound', '*.*'))),
                  ('locale', []),
                  ('locale/sv', []), ('locale/sv/LC_MESSAGES', glob.glob(os.path.join('locale/sv/LC_MESSAGES/*'))),
                  ('locale/da', []), ('locale/da/LC_MESSAGES', glob.glob(os.path.join('locale/da/LC_MESSAGES/*'))),
                  ('locale/de', []), ('locale/de/LC_MESSAGES', glob.glob(os.path.join('locale/de/LC_MESSAGES/*'))),
                  ('locale/fr', []), ('locale/fr/LC_MESSAGES', glob.glob(os.path.join('locale/fr/LC_MESSAGES/*'))),
                  ('locale/nl', []), ('locale/nl/LC_MESSAGES', glob.glob(os.path.join('locale/nl/LC_MESSAGES/*'))),
                  ('locale/ja', []), ('locale/ja/LC_MESSAGES', glob.glob(os.path.join('locale/ja/LC_MESSAGES/*'))),
                  ('locale/it', []), ('locale/it/LC_MESSAGES', glob.glob(os.path.join('locale/it/LC_MESSAGES/*'))),
                  ('locale/zh_CN', []), ('locale/zh_CN/LC_MESSAGES', glob.glob(os.path.join('locale/zh_CN/LC_MESSAGES/*'))),
                  ('docs', []),
                  ('docs/en', []), ('docs/en', glob.glob(os.path.join('docs/en/*.html'))),
                  ]

    setup(name="EasyABC",
      version=program_version,
      description=program_name,
      long_description=long_description,
      url=url,
      author=author,
      options=options,
      data_files=data_files,
      #executables=executables,
      **{buildstyle : [{'script' : 'easy_abc.py'}
                       ]}
      )

else:
    from cx_Freeze import setup, Executable
    base = "gui"
    icon = 'img\\EasyABC.ico'
    include_files = include_files + \
                    ['bin\\abc2midi.exe',
                     'bin\\abcm2ps.exe',
                     'bin\\midi2abc.exe',
                     'bin\\abc2abc.exe',
                     'bin\\nwc2xml.exe',
                     #'bin\\zlibwapi.dll',
                     #'bin\\FluidSynth\\X86\\libsndfile-1.dll',
                     #'bin\\FluidSynth\\X86\\intl.dll',
                     #'bin\\FluidSynth\\X86\\libfluidsynth-3.dll',
                     #'bin\\FluidSynth\\X86\\libglib-2.0-0.dll',
                     #'bin\\FluidSynth\\X86\\libgobject-2.0-0.dll',
                    # 'bin\\FluidSynth\\X86\\libgthread-2.0-0.dll',
                    # 'bin\\FluidSynth\\X86\\libinstpatch-2.dll',
                     'bin\\FluidSynth\\libfluidsynth-3.dll',
                     'bin\\FluidSynth\\SDL3.dll',
                     'bin\\FluidSynth\\sndfile.dll',
                     'reference.txt',
                     'gpl-license.txt',
                     ]

    # 1.3.7.1 [JWDJ] to maintain the folder structure make a tuple with same source and target path
    include_files = [x for x in include_files if not isinstance(x, basestring)] + [(x, x) for x in include_files if isinstance(x, basestring)] # maintain folder structure

    excludes = ['tkinter','tcl','tk','unittest','multiprocessing','pydoc_data',
        'curses', 'distutils', 'json', 'lib2to3', 'html5lib', 'numpy',
        'pkg_resources', 'setuptools', 'webencodings', 'pygame',
        'ssl', 'bz2', 'lzma',
        # 'email',  # needed by urllib
    ]
    includes = [
        # 'mechanize',
        # 'socket',
        'urllib'] #, 'win32api', 'win32process']

    # after running build.bat there should be no folders in build\exe.win*\lib
    # if there are folders then add the names to the excludes because the packages are probably not necessary for EasyABC
    # the packages that are necessary should be in zip_include_pkgs to reduce files (the files will be included in library.zip)
    zip_include_pkgs = ['wx', 'xml', 'collections', 'ctypes', 'email', 'encodings', 'html', 'http', 'importlib', 'logging', 'midi', 'urllib']

    options["build_exe"] = {'excludes': excludes,
                        'includes': includes,
                        'optimize': 1,
                        # 'no_compress': True,
                        'include_msvcr': True,
                        'zip_include_packages' : ','.join(zip_include_pkgs),
                        'include_files': include_files }

    executables = [Executable(
        script="easy_abc.py",
        base=base,
        icon=icon
    )]

    setup(name="EasyABC",
          version=program_version,
          description=program_name,
          long_description=long_description,
          url=url,
          author=author,
          options=options,
          executables=executables,
          )
