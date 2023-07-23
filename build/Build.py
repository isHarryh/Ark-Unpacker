# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, time, shutil

if __name__ == '__main__':
    # Settings
    app_info = {
        'name': 'ArkUnpacker',
        'version': '2.5.0',
        'company': 'by Harry Huang',
        'copyright': '©Harry Huang @BSD 3-Clause License'
    }
    build_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(os.path.realpath(build_dir))
    venv_dir = os.path.join(build_dir, 'venv')
    file_list = {
        'srcdir': os.path.join(project_dir, 'src'),
        'main': os.path.join(project_dir, 'Main.py'),
        'icon': os.path.join(project_dir, 'ArkUnpacker.ico'),
        'requirements': os.path.join(build_dir, 'requirements.txt')
    }
    post_copy = {
        os.path.join(build_dir, 'dlls', 'FMOD'): os.path.join(venv_dir, 'dist', 'Main', 'UnityPy', 'lib', 'FMOD')
    }
    pip_source = 'https://pypi.tuna.tsinghua.edu.cn/simple'

    ##########

    def run_cmd(cmd:str):
        rst = os.system(cmd)
        if rst == 0:
            print(f"[Done] <- {cmd}")
        else:
            print(f"[Error] <- {cmd}")
            input(f"× Build failed! CMD code {rst}")
            exit()

    def run_cmd_venv(cmd:str, venv_dir:str=venv_dir):
        cmd = f"{os.path.join(venv_dir, 'Scripts', 'activate')}&{cmd}"
        run_cmd(cmd)

    def get_version_file_content(app_info:dict):
        version_split = app_info['version'].split('.')
        return f'''# UTF-8
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
'''

    try:
        print('Preparing to build...')
        t1 = time.time()
        os.chdir(build_dir) # Work Dir: Build Dir
        shutil.rmtree(venv_dir, ignore_errors=True)
    
        print('Generateing environment...')
        run_cmd(f"python -m venv {venv_dir}")
        os.chdir(venv_dir) # Work Dir: Venv Dir

        print('Copying resources...')
        for src_key in file_list.keys():
            src = file_list[src_key]
            src_name = os.path.basename(src)
            if os.path.isdir(src):
                shutil.rmtree(src_name, ignore_errors=True)
                shutil.copytree(src, src_name)
            elif os.path.isfile(src):
                shutil.copy(src, src_name)

        print(f"Generateing version file... ({app_info['version']})")
        file_version = 'version.txt'
        with open(file_version, 'w', encoding='UTF-8') as f:
            f.write(get_version_file_content(app_info))

        print('Installing packages...')
        run_cmd_venv(f"Scripts{os.path.sep}activate&pip install -i {pip_source} -r {os.path.basename(file_list['requirements'])}")

        print('Running pyinstaller...')
        run_cmd_venv(f"pyinstaller -D -i {os.path.basename(file_list['icon'])} --version-file={file_version} {os.path.basename(file_list['main'])}")

        print('Copying additional files...')
        for src in post_copy.keys():
            if os.path.isdir(src):
                shutil.rmtree(post_copy[src], ignore_errors=True)
                shutil.copytree(src, post_copy[src])
            elif os.path.isfile(src):
                shutil.copy(src, post_copy[src])

        input(f"√ Build finished in {round(time.time() - t1, 1)}s!")
    except Exception as arg:
        input(f"× Build failed! Python exception: {arg}")
        raise arg
    exit()
