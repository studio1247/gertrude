# -*- mode: python -*-
a = Analysis(['gertrude.pyw'],
             datas=[
                 ("*.ini.dist", "."),
                 ("demo.db", "."),
                 ("*.php", "."),
                 ("bitmaps_dist\\*.png", "bitmaps_dist"),
                 ("bitmaps_dist\\pictos\\*.png", "bitmaps_dist\\pictos"),
                 ("bitmaps_dist\\*.ico", "bitmaps_dist"),
                 ("templates_dist\\*.html", "templates_dist"),
                 ("templates_dist\\*.txt", "templates_dist"),
                 ("templates_dist\\*.od?", "templates_dist")
             ],
             hiddenimports=["_cffi_backend"],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='gertrude.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='bitmaps_dist\\gertrude.ico' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='gertrude')
