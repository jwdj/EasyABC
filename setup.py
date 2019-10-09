#!/usr/bin/python2.7
# setup.py
from distutils.core import setup
import sys
import glob
import os.path
if sys.version_info.major > 2:
    basestring = str

version = '1.3.7.8'
description = "EasyABC"
long_description = "Nils Liberg's EasyABC 1.3.7 (Seymour Shlien)"
url = 'http://www.nilsliberg.se/ksp/easyabc/'
author = 'Nils Liberg'

options = {}
executables = []

include_files = [os.path.join('locale', 'sv', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'sv', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'da', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'da', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'fr', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'fr', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'nl', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'nl', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'ja', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'ja', 'LC_MESSAGES', 'easyabc.mo'),
                 os.path.join('locale', 'it', 'LC_MESSAGES', 'easyabc.po'),
                 os.path.join('locale', 'it', 'LC_MESSAGES', 'easyabc.mo')] + \
                 glob.glob(os.path.join('img', '*.*')) + glob.glob(os.path.join('sound', '*.*'))

if sys.platform == "darwin":
    import py2app
#    import bdist_mpkg
    buildstyle = 'app'
    options["py2app"] = {"argv_emulation" : False,
                         'iconfile'       : "img/EasyABC.icns",
        #                 'optimize'       : 1,  #2
                         'compressed'     : 0,
        #                 'excludes': ['Tkinter','tcl','tk','_ssl', 'email'],
                         'excludes': ['Tkinter','tcl','tk','_ssl', 'pygame', 'pygame.pypm'],
        #                 'includes': ['mechanize', 'urllib', 'socket', 'pygame.pypm' ],
                         'includes': ['mechanize', 'urllib', 'socket' ],
                         'packages': ['wx'],
                         'plist': {
                                   'CFBundleDocumentTypes': [{
                                                              'CFBundleTypeExtensions': ['abc'],
                                                              'CFBundleTypeName': 'ABC notation file',
                                                              'CFBundleTypeRole': 'Viewer'
                                                            }]
                                  }
                         }
    data_files = [('.', ['reference.txt', 'gpl-license.txt']),
                  ('bin', ['bin/abc2midi', 'bin/abcm2ps', 'bin/abc2abc', 'bin/nwc2xml', 'bin/midi2abc']),
                  ('img', glob.glob(os.path.join('img', '*.*'))),
                  ('sound', glob.glob(os.path.join('sound', '*.*'))),
                  ('locale', []),
                  ('locale/sv', []), ('locale/sv/LC_MESSAGES', glob.glob(os.path.join('locale/sv/LC_MESSAGES/*'))),
                  ('locale/da', []), ('locale/da/LC_MESSAGES', glob.glob(os.path.join('locale/da/LC_MESSAGES/*'))),
                  ('locale/fr', []), ('locale/fr/LC_MESSAGES', glob.glob(os.path.join('locale/fr/LC_MESSAGES/*'))),
                  ('locale/nl', []), ('locale/nl/LC_MESSAGES', glob.glob(os.path.join('locale/nl/LC_MESSAGES/*'))),
                  ('locale/ja', []), ('locale/ja/LC_MESSAGES', glob.glob(os.path.join('locale/ja/LC_MESSAGES/*'))),
                  ('locale/it', []), ('locale/it/LC_MESSAGES', glob.glob(os.path.join('locale/it/LC_MESSAGES/*'))),
                  ]

    setup(name="EasyABC",
      version=version,
      description=description,
      long_description=long_description,
      url=url,
      author=author,
      options=options,
      data_files=data_files,
      #executables=executables,
      **{buildstyle : [{'script' : 'easy_abc.py',
                     'icon_resources' : [(0, 'img/logo.ico')]}
                       ]}
      )

else:
    from cx_Freeze import setup, Executable
    base = "Win32GUI"
    icon = 'img\\logo.ico'
    include_files = include_files + \
                    ['bin\\abc2midi.exe',
                     'bin\\abcm2ps.exe',
                     'bin\\midi2abc.exe',
                     'bin\\abc2abc.exe',
                     'bin\\nwc2xml.exe',
                     'bin\\zlibwapi.dll',
                     'reference.txt',
                     'gpl-license.txt',
                     'easy_abc.exe.manifest',
                     'Microsoft.VC90.CRT\\Microsoft.VC90.CRT.manifest',
                     'Microsoft.VC90.CRT\\msvcm90.dll',
                     'Microsoft.VC90.CRT\\msvcp90.dll',
                     'Microsoft.VC90.CRT\\msvcr90.dll',]

    # 1.3.7.1 [JWDJ] to maintain the folder structure make a tuple with same source and target path
    include_files = [x for x in include_files if not isinstance(x, basestring)] + [(x, x) for x in include_files if isinstance(x, basestring)] # maintain folder structure

    options["build_exe"] = {'excludes': ['Tkinter','tcl','tk','_ssl', 'email'],   #, 'numpy.linalg.lapack_lite',  'numpy.random.mtrand.pyd', 'numpy.fft.fftpack_lite.pyd'],
                        'includes': ['mechanize', 'urllib', 'socket', 'win32api', 'win32process'],
                        'optimize': 1,
                        'include_files': include_files }

    executables = [Executable(
        script="easy_abc.py",
        base=base,
        icon=icon,
        copyDependentFiles = True,
        appendScriptToExe = False,
        appendScriptToLibrary = False,
    )]

    setup(name="EasyABC",
          version=version,
          description=description,
          long_description=long_description,
          url=url,
          author=author,
          options=options,
          executables=executables,
          )
