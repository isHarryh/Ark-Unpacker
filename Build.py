# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, sys, time, shutil

def __main():
    # Settings
    app_info = {
        'name': 'ArkUnpacker',
        'version': '3.0.0',
        'company': 'by Harry Huang',
        'copyright': '©Harry Huang @BSD 3-Clause License'
    }
    venv_dir = '.venv'
    requirements_file = 'requirements.txt'
    entry_file = 'Main.py'
    icon_file = 'ArkUnpacker.ico'
    post_copy = {
        os.path.join('build', 'dlls', 'FMOD'): os.path.join(venv_dir, 'dist', 'Main', 'UnityPy', 'lib', 'FMOD')
    }
    pip_source = 'https://pypi.tuna.tsinghua.edu.cn/simple'
    __build(venv_dir, app_info, entry_file, icon_file, post_copy=post_copy)
    for i in sys.argv[1:]:
        if i == 'clear':
            __clear(venv_dir)
            exit()
        elif i == 'setup':
            __setup(venv_dir, requirements_file, pip_source=pip_source)
            exit()
        elif i == 'build':
            __build(venv_dir, app_info, entry_file, icon_file, post_copy=post_copy)
            exit()
    print("× Argument required. Argument = [clear|setup|build]")
    exit()

def __exec(cmd):
    rst = os.system(cmd)
    if rst == 0:
        print(f"[Done] <- {cmd}")
    else:
        print(f"[Error] <- {cmd}")
        print(f"× Execution failed! Returned code: {rst}")
        exit()

def __clear(venv_dir):
    shutil.rmtree(venv_dir, ignore_errors=True)
    print("√ Cleared!")

def __setup(venv_dir, requirements_file, pip_source=None):
    t1 = time.time()
    if os.path.isdir(venv_dir):
        print("Venv dir existed")
    else:
        print("Generating venv dir...")
        __exec(f"python -m venv {venv_dir}")
    
    print("Solving dependencies...")
    cmd_activate = os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin', 'activate')
    cmd_pip = f"pip install -r {requirements_file}{f' -i {pip_source}' if pip_source else ''}"
    __exec(f"{cmd_activate} && {cmd_pip}")
    
    print(f"√ Setup finished in {round(time.time() - t1, 1)}s!")

def __build(venv_dir, app_info, entry_file, icon_file, post_copy={}):
    t1 = time.time()
    try:
        if not os.path.isdir(venv_dir):
            print("No venv dir exists. Run setup first.")
            raise FileNotFoundError(f"{venv_dir} dir not found")
        
        print(f"Generating version file... ({app_info['version']})")
        version_file = 'version.txt'
        with open(version_file, 'w', encoding='UTF-8') as f:
            version_split = app_info['version'].split('.')
            f.write(f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
filevers=({version_split[0]},{version_split[1]},{version_split[2]}, 0),
prodvers=(0, 0, 0, 0),
mask=0x3f,
flags=0x0,
OS=0x4,
fileType=0x1,
subtype=0x0,
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'{app_info['company']}'),
    StringStruct(u'FileDescription', u'{app_info['name']}'),
    StringStruct(u'FileVersion', u'{version_split[0]}.{version_split[1]}'),
    StringStruct(u'LegalCopyright', u'{app_info['copyright']}'),
    StringStruct(u'ProductName', u'{app_info['name']}'),
    StringStruct(u'ProductVersion', u'{version_split[0]}.{version_split[1]}')])
  ]),
VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
''') # End f.write
        
        print('Running pyinstaller...')
        cmd_activate = os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin', 'activate')
        cmd_pyinstaller = f"pyinstaller -D -i {icon_file} --version-file={version_file} {entry_file}"
        __exec(f"{cmd_activate} && {cmd_pyinstaller}")

        print('Copying additional files...')
        for src in post_copy.keys():
            if os.path.isdir(src):
                shutil.rmtree(post_copy[src], ignore_errors=True)
                shutil.copytree(src, post_copy[src])
            elif os.path.isfile(src):
                shutil.copy(src, post_copy[src])
            else:
                print("Additional file or dir not found.")
                raise FileNotFoundError(f"{src} not found")

        
        print(f"√ Build finished in {round(time.time() - t1, 1)}s!")
    except Exception as arg:
        print(f"× Build failed! Python exception: {arg}")
        raise arg

if __name__ == '__main__':
    __main()
