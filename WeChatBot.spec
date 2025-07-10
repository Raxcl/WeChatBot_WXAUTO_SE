# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('templates', 'templates'), ('prompts', 'prompts'), ('emojis', 'emojis')]
datas += collect_data_files('wxautox_wechatbot')
datas += collect_data_files('database')
datas += collect_data_files('ai_platforms')


a = Analysis(
    ['bot.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['wxautox_wechatbot', 'wxautox_wechatbot.logger', 'wxautox_wechatbot.param', 'wxautox_wechatbot.languages', 'wxautox_wechatbot.uiautomation', 'comtypes', 'pywin32', 'win32api', 'win32con', 'win32gui', 'win32process', 'pywintypes', 'tenacity', 'tenacity.retry', 'tenacity.stop', 'tenacity.wait', 'openai', 'httpx', 'httpcore', 'h11', 'anyio', 'sniffio', 'sqlalchemy', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.pool', 'database', 'database.models', 'database.database', 'requests', 'beautifulsoup4', 'bs4', 'pyautogui', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'json', 'queue', 'threading', 'logging', 'datetime', 'base64', 'urllib.parse', 'ai_platforms', 'ai_platforms.manager', 'ai_platforms.platform_router', 'ai_platforms.base_platform', 'ai_platforms.coze_platform', 'ai_platforms.llm_direct'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('v', None, 'OPTION')],
    name='WeChatBot',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
