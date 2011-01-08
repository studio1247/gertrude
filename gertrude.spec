# -*- mode: python -*-
import glob

a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'gertrude.pyw'] + glob.glob('panel_*.py'),
             pathex=['C:\\Users\\Bertrand\\workspace\\gertrude'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\gertrude', 'gertrude.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='bitmaps_dist\\gertrude.ico' )
coll = COLLECT( exe,
               a.binaries + [(x, x, 'DATA') for x in glob.glob("*.ini.dist") + glob.glob("*.php") + glob.glob("bitmaps_dist\\*.png") + glob.glob("bitmaps_dist\\*.ico") + glob.glob("templates_dist\\*.html") + glob.glob("templates_dist\\*.od?") + glob.glob("doc\\*")],
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=os.path.join('dist', 'gertrude'))   
hiddenimports=['win32api', 'win32com', 'win32com.client', 'win32com.client.gencache']

