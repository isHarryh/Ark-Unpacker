# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, configparser

def __get_venv_dir():
    import re, subprocess
    rst = subprocess.run(['poetry', 'env', 'info'], capture_output=True, text=True)
    
    if rst.returncode == 0:
        for l in rst.stdout.splitlines():
            match = re.search(r'Path:\s+(.+)', l)
            if match:
                path = match.group(1).strip()
                if os.path.isdir(path):
                    return path
        print("× Failed to parse poetry output to query venv dir.")
    else:
        print(f"× Failed to run poetry to query venv dir. Returned code: {rst.returncode}")
    print("- Please check the compatibility of poetry version.")
    print("- Please check the poetry status and the venv info.")
    raise Exception("venv dir not found or poetry config failed")

def __get_proj_info():
    try:
        parser = configparser.ConfigParser()
        parser.read('pyproject.toml', encoding='UTF-8')
        config = parser['tool.poetry']
        return {
            'name': config['name'].strip("'\""),
            'version': config['version'].strip("'\""),
            'description': config['description'].strip("'\""),
            'author': config['authors'].strip("'\"[]").split('<')[0].strip(),
            'license': config['license'].strip("'\"").replace('\\\\', '\\')
        }
    except Exception as arg:
        print("× Failed to parse poetry project info.")
        raise arg

def __get_build_def():
    try:
        parser = configparser.ConfigParser()
        parser.read('pyproject.toml', encoding='UTF-8')
        config = parser['tool.build']
        return {
            'entry': config['entry'].strip("'\""),
            'icon': config['icon'].strip("'\""),
            'add-binary': config['add-binary'].strip("'\""),
            'build-dir': config['build-dir'].strip("'\""),
            'log-level': config['log-level'].strip("'\"")
        }
    except Exception as arg:
        print("× Failed to parse build definition fields.")
        raise arg

def __main():
    venv_dir = __get_venv_dir()
    proj_info = __get_proj_info()
    build_def = __get_build_def()
    print(f"Project: {proj_info['name']}|{proj_info['version']}|{proj_info['author']}|{proj_info['license']}")
    print(f"Venv: {venv_dir}")
    print("")
    __build(venv_dir, proj_info, build_def)
    exit(0)

def __exec(cmd):
    rst = os.system(cmd)
    if rst == 0:
        print(f"\n[Done] <- {cmd}")
    else:
        print(f"\n[Error] <- {cmd}")
        print(f"× Execution failed! Returned code: {rst}")
        exit(1)

def __build(venv_dir, proj_info, build_def):
    import time, shutil
    t1 = time.time()
    proj_dir = os.path.dirname(os.path.abspath(__file__))
    for k, v in build_def.items():
        build_def[k] = v.replace('\\\\', '\\').replace('$project$', proj_dir).replace('$venv$', venv_dir)
    
    print(f"Removing build dir...")
    os.chdir(proj_dir)
    build_dir = build_def['build-dir']
    shutil.rmtree(build_dir, ignore_errors=True)

    print(f"Creating build dir...")
    os.mkdir(build_dir)
    os.chdir(build_dir)
    
    print(f"Creating version file...")
    version_file = 'version.txt'
    with open(version_file, 'w', encoding='UTF-8') as f:
        f.write(f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
filevers=({proj_info['version'].replace('.',',')},0),
prodvers=({proj_info['version'].replace('.',',')},0),
mask=0x3f,
flags=0x0,
OS=0x4,
fileType=0x1,
subtype=0x0,
date=(0,0)
),
  kids=[
StringFileInfo([
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'{proj_info['author']}'),
    StringStruct(u'FileDescription', u'{proj_info['description']}'),
    StringStruct(u'FileVersion', u'{proj_info['version']}'),
    StringStruct(u'LegalCopyright', u'©{proj_info['author']} @{proj_info['license']} License'),
    StringStruct(u'ProductName', u'{proj_info['name']}'),
    StringStruct(u'ProductVersion', u'{proj_info['version']}')])
  ])
])
''') # End f.write
    
    print('Running pyinstaller...')
    cmd_pyinstaller = f"poetry run pyinstaller -F"
    cmd_pyinstaller += f" -i \"{build_def['icon']}\""
    cmd_pyinstaller += f" --name \"{proj_info['name']}-v{proj_info['version']}\""
    cmd_pyinstaller += f" --version-file {version_file}"
    cmd_pyinstaller += f" --add-binary \"{build_def['add-binary']}\""
    cmd_pyinstaller += f" --log-level {build_def['log-level']}"
    cmd_pyinstaller += f" \"{build_def['entry']}\""
    __exec(cmd_pyinstaller)

    print(f"√ Build finished in {round(time.time() - t1, 1)}s!")
    print(f"- Dist files see: {os.path.join(build_dir, 'dist')}")

if __name__ == '__main__':
    __main()
