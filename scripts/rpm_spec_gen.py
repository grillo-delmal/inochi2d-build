#!/usr/bin/python3

import json
import subprocess
import shutil
import math

from pathlib import Path
from spec_gen_util import LibData, LibSpecFile

removed_deps = ['openssl-static']

def find_deps(parent, dep_graph):
    deps = set(dep_graph[parent]['dependencies'])
    for name in dep_graph[parent]['dependencies']:
        deps = deps.union(find_deps(name, dep_graph))
    return deps

data = {}
with open("build_out/creator-describe") as f:
    data = json.load(f)

creator_dep_graph = {
    package['name']: package 
        for package in data['packages'] if package['name'] not in removed_deps }
for name in creator_dep_graph.keys():
    creator_dep_graph[name]['dependencies'] = [dep for dep in creator_dep_graph[name]['dependencies'] if dep not in removed_deps]

creator_deps = list(find_deps("inochi-creator", creator_dep_graph))
creator_deps.sort()
print("All creator deps", creator_deps)

data = {}
with open("build_out/session-describe") as f:
    data = json.load(f)

session_dep_graph = {
    package['name']: package 
        for package in data['packages'] if package['name'] not in removed_deps }
for name in session_dep_graph.keys():
    session_dep_graph[name]['dependencies'] = [dep for dep in session_dep_graph[name]['dependencies'] if dep not in removed_deps]

session_deps = list(find_deps("inochi-session", session_dep_graph))
session_deps.sort()
print("All session deps", session_deps)

# Find creator libs
creator_project_libs = []
project_deps = {
    name: creator_dep_graph[name] 
        for name in creator_dep_graph.keys() 
        if creator_dep_graph[name]['path'].startswith(
            '/opt/deps/') and \
        name in creator_deps}

pd_names = list(project_deps.keys())
pd_names.sort()
print("Direct creator deps found", pd_names)

for name in pd_names:
    NAME = project_deps[name]['name'].replace('-', '_').lower()
    SEMVER = project_deps[name]['version']
    GITPATH = project_deps[name]['path'].replace("/opt/deps","./src")
    COMMIT = subprocess.run(
        ['git', '-C', GITPATH, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITVER = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_version ' + GITPATH],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITDIST = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_build ' + GITPATH],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    SOURCE_BASE_URL= subprocess.run(
        ['git', '-C', GITPATH, 'config', '--get', 'remote.origin.url'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()[:-4]

    extra_consts={}

    if name == "i2d-imgui":
        imgui_data = {}
        with open("build_out/i2d-imgui-state") as f:
            imgui_data = json.load(f)

        extra_consts={
            "cimgui_commit":imgui_data["cimgui"],
            "cimgui_short":imgui_data["cimgui"][:7],
            "imgui_commit":imgui_data["imgui"],
            "imgui_short":imgui_data["imgui"][:7]
        }

    creator_project_libs.append(
        LibData(
            name, 
            list(
                { 
                    dep.split(':')[0] 
                        for dep in project_deps[name]['dependencies']
                }), 
            GITVER,
            SEMVER, 
            GITDIST,
            COMMIT,
            SOURCE_BASE_URL + ("/archive/%%{%s_commit}/%s-%%{%s_short}.tar.gz" % (NAME, NAME, NAME)),
            extra_consts=extra_consts)            
        )

# Find session libs
session_project_libs = []
project_deps = {
    name: session_dep_graph[name] 
        for name in session_dep_graph.keys() 
        if session_dep_graph[name]['path'].startswith(
            '/opt/deps/') and \
        name in session_deps}

pd_names = list(project_deps.keys())
pd_names.sort()
print("Direct session deps found", pd_names)

for name in pd_names:
    NAME = project_deps[name]['name'].replace('-', '_').lower()
    SEMVER = project_deps[name]['version']
    GITPATH = project_deps[name]['path'].replace("/opt/deps","./src")
    COMMIT = subprocess.run(
        ['git', '-C', GITPATH, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITVER = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_version ' + GITPATH],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITDIST = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_build ' + GITPATH],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    SOURCE_BASE_URL= subprocess.run(
        ['git', '-C', GITPATH, 'config', '--get', 'remote.origin.url'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()[:-4]

    extra_consts={}

    if name == "i2d-imgui":
        imgui_data = {}
        with open("build_out/i2d-imgui-state") as f:
            imgui_data = json.load(f)

        extra_consts={
            "cimgui_commit":imgui_data["cimgui"],
            "cimgui_short":imgui_data["cimgui"][:7],
            "imgui_commit":imgui_data["imgui"],
            "imgui_short":imgui_data["imgui"][:7]
        }

    session_project_libs.append(
        LibData(
            name, 
            list(
                { 
                    dep.split(':')[0] 
                        for dep in project_deps[name]['dependencies']
                }), 
            GITVER,
            SEMVER, 
            GITDIST,
            COMMIT,
            SOURCE_BASE_URL + "/archive/%%{%{name}_commit}/%{name}-%%{%{name}_short}.tar.gz",
            extra_consts=extra_consts)            
        )

# Find indirect creator deps
indirect_deps = {
    name: creator_dep_graph[name] 
        for name in creator_dep_graph.keys() 
        if not creator_dep_graph[name]['path'].startswith(
            '/opt/deps/') and \
        name in creator_deps}

id_names = list(indirect_deps.keys())
id_names.sort()
print("Indirect creator deps found", id_names)
for id_name in id_names:
    print("  %s: %s" % (id_name, indirect_deps[id_name]["dependencies"]))

creator_true_deps = {}
creator_true_names = []

for name in id_names:
    NAME = indirect_deps[name]['name'].lower()
    TRUENAME = NAME.split(":")[0]
    SEMVER = indirect_deps[name]['version']

    if TRUENAME in creator_true_deps:
        creator_true_deps[TRUENAME].append({"name": NAME, "semver":SEMVER})
    else:
        creator_true_deps[TRUENAME] = [{"name": NAME, "semver":SEMVER}]
        creator_true_names.append(TRUENAME)

creator_true_names.sort()

# Find indirect session deps
indirect_deps = {
    name: session_dep_graph[name] 
        for name in session_dep_graph.keys() 
        if not session_dep_graph[name]['path'].startswith(
            '/opt/deps/') and \
        name in session_deps}

id_names = list(indirect_deps.keys())
id_names.sort()
print("Indirect session deps found", id_names)
for id_name in id_names:
    print("  %s: %s" % (id_name, indirect_deps[id_name]["dependencies"]))

session_true_deps = {}
session_true_names = []

for name in id_names:
    NAME = indirect_deps[name]['name'].lower()
    TRUENAME = NAME.split(":")[0]
    SEMVER = indirect_deps[name]['version']

    if TRUENAME in session_true_deps:
        session_true_deps[TRUENAME].append({"name": NAME, "semver":SEMVER})
    else:
        session_true_deps[TRUENAME] = [{"name": NAME, "semver":SEMVER}]
        session_true_names.append(TRUENAME)

session_true_names.sort()

true_names = list(set(creator_true_names + session_true_names))
true_names.sort()

creator_indirect_libs = []
session_indirect_libs = []

for name in true_names:

    # Copy build files into destination folder
    Path("build_out/rpms/zdub-deps/zdub-%s"  % name).mkdir(parents=True, exist_ok=True)
    for file in Path("files/%s" % name).glob("**/*"):
        if file.is_file():
            shutil.copy(file, "build_out/rpms/zdub-deps/zdub-%s/" % name)

    # Also copy patches
    for file in Path("patches/%s" % name).glob("*.patch"):
        shutil.copy(file, "build_out/rpms/zdub-deps/zdub-%s/" % name)

    id_deps = set()

    if name in creator_true_names:
        # Find creator lib dependencies
        SEMVER = creator_true_deps[name][0]["semver"]

        for dep in creator_true_deps[name]:
            id_deps = id_deps.union(set(creator_dep_graph[dep["name"]]['dependencies']))
            SEMVER = dep["semver"]
            pass

    elif name in session_true_names:
        # Find session lib dependencies
        SEMVER = session_true_deps[name][0]["semver"]

        for dep in session_true_deps[name]:
            id_deps = id_deps.union(set(session_dep_graph[dep["name"]]['dependencies']))
            SEMVER = dep["semver"]
            pass

    for dep in list(id_deps):
        dep_truename = dep.split(":")[0]
        if dep_truename != dep:
            id_deps.remove(dep)
            if dep_truename != name:
                id_deps.add(dep_truename)
    
    # Write specfile
    extra_consts={}

    if name == "i2d-imgui":
        imgui_data = {}
        with open("build_out/i2d-imgui-state") as f:
            imgui_data = json.load(f)

        extra_consts={
            "cimgui_commit":imgui_data["cimgui"],
            "cimgui_short":imgui_data["cimgui"][:7],
            "imgui_commit":imgui_data["imgui"],
            "imgui_short":imgui_data["imgui"][:7]
        }

    lib_spec = LibSpecFile(
        name, 
        list(
            { 
                dep.split(':')[0] 
                    for dep in list(id_deps)
            }), 
        SEMVER,
        extra_consts=extra_consts)

    lib_spec.spec_gen(
                "build_out/rpms/zdub-deps/zdub-%s/zdub-%s.spec" % (name, name))

    if name in creator_true_names:
        creator_indirect_libs.append(lib_spec)

    if name in session_true_names:
        session_indirect_libs.append(lib_spec)

# Write inochi-creator.spec
Path("build_out/rpms/inochi-creator-rpm/").mkdir(parents=True, exist_ok=True)
with open("build_out/rpms/inochi-creator-rpm/inochi-creator.spec", 'w') as spec:

    # Copy creator files and patches patches
    for file in Path("files/%s" % "inochi-creator").glob("**/*"):
        if file.is_file():
            shutil.copy(file, "build_out/rpms/inochi-creator-rpm/")
    for file in Path("patches/%s" % "inochi-creator").glob("*.patch"):
        if file.is_file():
            shutil.copy(file, "build_out/rpms/inochi-creator-rpm/")

    # Copy creator files and patches patches
    for lib in creator_project_libs:
        for file in Path("files/%s" % lib.name).glob("**/*"):
            if file.is_file():
                Path("build_out/rpms/inochi-creator-rpm/files/%s" % lib.name).mkdir(parents=True, exist_ok=True)
                shutil.copy(file, "build_out/rpms/inochi-creator-rpm/files/%s/" % lib.name)
        for file in Path("patches/%s" % lib.name).glob("*.patch"):
            if file.is_file():
                shutil.copy(file, "build_out/rpms/inochi-creator-rpm/")

    # CONSTS
    SEMVER = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/semver.sh;' + \
            'semver ./src/inochi-creator'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    COMMIT = subprocess.run(
        'git -C ./src/inochi-creator rev-parse HEAD'.split(),
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITVER = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_version ./src/inochi-creator'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITDIST = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_build ./src/inochi-creator'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

    spec.write('\n'.join([
        "%%define inochi_creator_ver %s" % GITVER,
        "%%define inochi_creator_semver %s" % SEMVER,
        "%%define inochi_creator_dist %s" % GITDIST,
        "%%define inochi_creator_commit %s" % COMMIT,
        "%%define inochi_creator_short %s" % COMMIT[:7],
        "",
        ""]))

    if len(creator_project_libs) > 0:
        spec.write('\n'.join([
            '# Project maintained deps',
            ""]))

        for lib in creator_project_libs:
            NAME = lib.name.replace('-', '_').lower()

            spec.write('\n'.join([
                "%%define %s_semver %s" % (NAME, lib.semver),
                "%%define %s_commit %s" % (NAME, lib.commit),
                "%%define %s_short %s" % (NAME, lib.commit[:7]),
                ""]))

            for key in lib.extra_consts.keys():
                spec.write('\n'.join([
                    "%%define %s%s %s" % (
                        key,
                        " " * (13-len(key)),
                        lib.extra_consts[key]) ,
                    ""
                ]))
            spec.write('\n')

    # WRITING HEAD
    spec.write('\n'.join([line[8:] for line in '''\
        %if 0%{inochi_creator_dist} > 0
        %define inochi_creator_suffix ^%{inochi_creator_dist}.git%{inochi_creator_short}
        %endif

        Name:           inochi-creator
        Version:        %{inochi_creator_ver}%{?inochi_creator_suffix:}
        Release:        %autorelease
        Summary:        Tool to create and edit Inochi2D puppets

        '''.splitlines()]))

    # LICENSES

    # List direct licenses
    spec.write('\n'.join([
        "# Bundled lib licenses",
        ""]))        
    spec.write('\n'.join([
        "##   %s licenses: %s" % (
            lib.name, 
            ' and '.join(lib.licenses)
            ) for lib in creator_project_libs]))
    spec.write('\n')

    # List static dependency licenses
    spec.write('\n'.join([
        "# Static dependencies licenses",
        ""]))        
    spec.write('\n'.join([
        "##   %s licenses: %s" % (
            lib.name, 
            ' and '.join(lib.licenses)
        ) for lib in creator_indirect_libs]))
    spec.write('\n')

    # Add license field

    licenses = list(set().union(
        *[lib.licenses for lib in creator_project_libs],
        *[lib.licenses for lib in creator_indirect_libs]))
    licenses.sort()
    licenses.remove("BSD-2-Clause")
    licenses.insert(0, "BSD-2-Clause")
    
    spec.write('\n'.join([
        "License:        %s" % ' and '.join(licenses),
        "",
        ""]))

    spec.write('\n'.join([line[8:] for line in '''\
        URL:            https://github.com/grillo-delmal/inochi-creator-rpm

        #https://github.com/Inochi2D/inochi-creator/archive/{inochi_creator_commit}/{name}-{inochi_creator_short}.tar.gz
        Source0:        %{name}-%{version}-norestricted.tar.gz
        Source1:        config.d
        Source2:        icon.png
    
        '''.splitlines()]))

    # OTHER SOURCES
    spec.write('\n'.join([
        "# Project maintained deps",
        ""]))

    src_cnt = 3

    for lib in creator_project_libs:
        spec.write('\n'.join([
            "Source%d:%s%s" % (
                src_cnt, 
                " " * (8 - math.floor(math.log10(src_cnt) if src_cnt > 0 else 0)), 
                lib.source) ,
            ""
        ]))
        src_cnt += 1
        for src in lib.ex_sources:
            spec.write('\n'.join([
                "Source%d:%s%s" % (
                    src_cnt, 
                    " " * (8 - math.floor(math.log10(src_cnt))), 
                    src) ,
                ""
            ]))
            src_cnt += 1
        if len(lib.file_sources) > 0:
            for src in lib.file_sources:
                spec.write('\n'.join([
                    "Source%d:%sfiles/%s/%s" % (
                        src_cnt, 
                        " " * (8 - math.floor(math.log10(src_cnt))), 
                        lib.name,
                        src["name"]) ,
                    ""
                ]))
            src_cnt += 1
    spec.write('\n')

    # PATCHES
    ptch_cnt = 0

    patch_list = []
    if Path("patches/%s" % "inochi-creator").exists():
        patch_list = list(Path("patches/%s" % "inochi-creator").glob("*.patch"))
        patch_list.sort()
    for file in patch_list:
        spec.write('\n'.join([
            "Patch%d:%s%s" % (
                ptch_cnt, 
                " " * (9 - math.floor(math.log10(ptch_cnt) if ptch_cnt > 0 else 0)), 
                file.name) ,
            ""
        ]))
        ptch_cnt += 1

    # OTHER PATCHES
    for lib in creator_project_libs:
        for patch in lib.patches:
            spec.write('\n'.join([
                "Patch%d:%s%s" % (
                    ptch_cnt, 
                    " " * (9 - math.floor(math.log10(ptch_cnt) if ptch_cnt > 0 else 0)), 
                    patch) ,
                ""
            ]))
            ptch_cnt += 1
    spec.write('\n')

    # DEPS

    spec.write('\n'.join([line[8:] for line in '''\
        # dlang
        BuildRequires:  ldc
        BuildRequires:  dub
        BuildRequires:  jq

        BuildRequires:  desktop-file-utils
        BuildRequires:  libappstream-glib
        BuildRequires:  git

        BuildRequires:  zdub-dub-settings-hack
        '''.splitlines()]))

    spec.write('\n'.join([
        "BuildRequires:  zdub-%s-static" % lib.name \
            for lib in creator_indirect_libs]))

    spec.write('\n')
    spec.write('\n')
    for lib in creator_project_libs:

        if len(lib.build_reqs) > 0:
            spec.write('\n'.join([
                "#%s deps" % lib.name ,
                ""
            ]))
            for build_req in lib.build_reqs:
                spec.write('\n'.join([
                    "BuildRequires:  %s" % build_req ,
                    ""
                ]))
            spec.write('\n')

    spec.write('\n'.join([
        "Requires:       hicolor-icon-theme",
        ""]))
    spec.write('\n')

    for lib in creator_project_libs:
        if len(lib.requires) > 0:
            spec.write('\n'.join([
                "#%s deps" % lib.name ,
                ""
            ]))
            for req in lib.requires:
                spec.write('\n'.join([
                    "Requires:       %s" % req ,
                    ""
                ]))
            spec.write('\n')
    spec.write('\n')

    spec.write('\n'.join([line[8:] for line in '''\
        %description
        Inochi2D is a framework for realtime 2D puppet animation which can be used for VTubing, 
        game development and digital animation. 
        Inochi Creator is a tool that lets you create and edit Inochi2D puppets.
        This is an unbranded build, unsupported by the official project.


        '''.splitlines()]))

    # PREP
    spec.write('\n'.join([line[8:] for line in '''\
        %prep
        %setup -n %{name}-%{inochi_creator_commit}

        '''.splitlines()]))

    # GENERIC FIXES
    spec.write('\n'.join([line[8:] for line in '''\
        # FIX: Inochi creator version dependent on git
        cat > source/creator/ver.d <<EOF
        module creator.ver;

        enum INC_VERSION = "%{inochi_creator_semver}";
        EOF

        # FIX: Replace config.d and banner.png
        rm source/creator/config.d
        cp %{SOURCE1} source/creator/
        cp res/ui/grid.png res/ui/banner.png

        # FIX: Add fake dependency
        mkdir -p deps/vibe-d
        cat > deps/vibe-d/dub.sdl <<EOF
        name "vibe-d"
        subpackage "http"
        EOF
        dub add-local deps/vibe-d "0.9.5"

        '''.splitlines()]))

    src_cnt = 3
    ptch_cnt = 0

    patch_list = []
    if Path("patches/%s" % "inochi-creator").exists():
        patch_list = list(Path("patches/%s" % "inochi-creator").glob("*.patch"))
        patch_list.sort()
    for file in patch_list:
        spec.write('\n'.join([
            "%%patch -P %d -p1 -b .%s-%s" % (
                ptch_cnt,
                *list(file.name[:-6].split("_")[0::2])),
            ""
        ]))
        ptch_cnt += 1

    # PREP DEPS
    spec.write('\n'.join([line[8:] for line in '''\
        mkdir -p deps

        # Project maintained deps
        '''.splitlines()]))

    for lib in creator_project_libs:
        spec.write('\n'.join([
            "tar -xzf %%{SOURCE%d}" % src_cnt,
            "mv %s deps/%s" % (
                lib.prep_file, lib.name), 
            "dub add-local deps/%s/ \"%%{%s_semver}\"" % (
                lib.name, lib.name.replace('-', '_').lower()),
            ""
        ]))
        src_cnt += 1

        spec.write('\n')
        spec.write('\n'.join([
            "pushd deps; pushd %s" % lib.name,
            ""
            ]))
        if len(lib.patches) > 0:
            spec.write('\n')
            for patch in lib.patches:
                spec.write('\n'.join([
                    "%%patch -P %d -p1 -b .%s-%s" % (
                        ptch_cnt,
                        *list(patch[:-6].split("_")[0::2])),
                    ""
                ]))
                ptch_cnt += 1

        if len(lib.file_sources) > 0:
            spec.write("\n")
            for i in range(len(lib.file_sources)):
                if lib.file_sources[i]["path"] != ".":
                    spec.write('\n'.join([
                        "mkdir -p ./%s" % lib.file_sources[i]["path"],
                        "cp --force %%{SOURCE%d} ./%s/" % (src_cnt, lib.file_sources[i]["path"]),
                        ""
                    ]))
                else:
                    spec.write('\n'.join([
                        "cp %%{SOURCE%d} ." % (src_cnt),
                        ""
                    ]))
                src_cnt += 1

        if len(lib.prep) > 0:
            prep = '\n'.join(lib.prep)
            c = 1
            while prep.find("%%{SOURCE%d}" % c) > 0:
                prep = prep.replace("%%{SOURCE%d}" % c, "%%{SOURCE%d}" % src_cnt)
                src_cnt += 1
                c += 1

            spec.write("\n")
            spec.write(prep)


        spec.write('\n'.join([
            "",
            "[ -f dub.sdl ] && dub convert -f json",
            "mv -f dub.json dub.json.base",
            "jq 'walk(if type == \"object\" then with_entries(select(.key | test(\"preBuildCommands*\") | not)) else . end)' dub.json.base > dub.json",
            ""
        ]))

        spec.write('\n'.join([
            "",
            "popd; popd",
            ""
            ]))

        spec.write('\n')

    spec.write('\n')

    # BUILD
    spec.write('\n'.join([line[8:] for line in '''\
        %build
        export DFLAGS="%{_d_optflags}"
        dub build \\
            --cache=local \\
            --config=barebones \\
            --skip-registry=all \\
            --non-interactive \\
            --temp-build \\
            --compiler=ldc2
        mkdir ./out/
        cp /tmp/.dub/build/inochi-creator*/barebones*/* ./out/


        '''.splitlines()]))

    # INSTALL

    spec.write('\n'.join([line[8:] for line in '''\
        %install
        install -d ${RPM_BUILD_ROOT}%{_bindir}
        install -p ./out/inochi-creator ${RPM_BUILD_ROOT}%{_bindir}/inochi-creator

        install -d ${RPM_BUILD_ROOT}%{_datadir}/applications/
        install -p -m 644 ./build-aux/linux/inochi-creator.desktop ${RPM_BUILD_ROOT}%{_datadir}/applications/inochi-creator.desktop
        desktop-file-validate \\
            ${RPM_BUILD_ROOT}%{_datadir}/applications/inochi-creator.desktop

        install -d ${RPM_BUILD_ROOT}%{_metainfodir}/
        install -p -m 644 ./build-aux/linux/inochi-creator.appdata.xml ${RPM_BUILD_ROOT}%{_metainfodir}/inochi-creator.appdata.xml
        appstream-util validate-relax --nonet \\
            ${RPM_BUILD_ROOT}%{_metainfodir}/inochi-creator.appdata.xml

        install -d $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/256x256/apps/
        install -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/256x256/apps/inochi-creator.png

        '''.splitlines()]))
    
    # INSTALL LICENSES
    spec.write('\n'.join([line[8:] for line in '''\
        # Dependency licenses
        install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/deps/
        find ./deps/ -mindepth 1 -maxdepth 1 -exec \\
            install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/{} ';'

        find ./deps/ -mindepth 2 -maxdepth 2 -iname '*LICENSE*' -exec \\
            install -p -m 644 "{}" "${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/{}" ';'

        install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/res/
        find ./res/ -mindepth 1 -maxdepth 1 -iname '*LICENSE*' -exec \\
            install -p -m 644 {} ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/{} ';'


        '''.splitlines()]))

    # FILES
    spec.write('\n'.join([line[8:] for line in '''\
        %files
        %license LICENSE
        %{_datadir}/licenses/%{name}/*
        %{_bindir}/inochi-creator
        %{_metainfodir}/inochi-creator.appdata.xml
        %{_datadir}/applications/inochi-creator.desktop
        %{_datadir}/icons/hicolor/256x256/apps/inochi-creator.png


        %changelog
        %autochangelog
        '''.splitlines()][:-1]))

# Write inochi-session.spec
Path("build_out/rpms/inochi-session-rpm/").mkdir(parents=True, exist_ok=True)
with open("build_out/rpms/inochi-session-rpm/inochi-session.spec", 'w') as spec:

    # Copy session files and patches patches
    for file in Path("files/%s" % "inochi-session").glob("**/*"):
        if file.is_file():
            shutil.copy(file, "build_out/rpms/inochi-session-rpm/")
    for file in Path("patches/%s" % "inochi-session").glob("*.patch"):
        if file.is_file():
            shutil.copy(file, "build_out/rpms/inochi-session-rpm/")

    # Copy session files and patches patches
    for lib in session_project_libs:
        for file in Path("files/%s" % lib.name).glob("**/*"):
            if file.is_file():
                shutil.copy(file, "build_out/rpms/inochi-session-rpm/")
        for file in Path("patches/%s" % lib.name).glob("*.patch"):
            if file.is_file():
                shutil.copy(file, "build_out/rpms/inochi-session-rpm/")

    # CONSTS
    SEMVER = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/semver.sh;' + \
            'semver ./src/inochi-session'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    COMMIT = subprocess.run(
        'git -C ./src/inochi-session rev-parse HEAD'.split(),
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITVER = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_version ./src/inochi-session'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    GITDIST = subprocess.run(
        ['bash', '-c', 
            'source ./scripts/gitver.sh;' + \
            'git_build ./src/inochi-session'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

    spec.write('\n'.join([
        "%%define inochi_session_ver %s" % GITVER,
        "%%define inochi_session_semver %s" % SEMVER,
        "%%define inochi_session_dist %s" % GITDIST,
        "%%define inochi_session_commit %s" % COMMIT,
        "%%define inochi_session_short %s" % COMMIT[:7],
        "",
        ""]))

    spec.write('\n'.join([
        '# Project maintained deps',
        ""]))

    for lib in session_project_libs:
        NAME = lib.name.replace('-', '_').lower()

        spec.write('\n'.join([
            "%%define %s_semver %s" % (NAME, lib.semver),
            "%%define %s_commit %s" % (NAME, lib.commit),
            "%%define %s_short %s" % (NAME, lib.commit[:7]),
            "",
            ""]))

    # WRITING HEAD
    spec.write('\n'.join([line[8:] for line in '''\
        %if 0%{inochi_session_dist} > 0
        %define inochi_session_suffix ^%{inochi_session_dist}.git%{inochi_session_short}
        %endif

        Name:           inochi-session
        Version:        %{inochi_session_ver}%{?inochi_session_suffix:}
        Release:        %autorelease
        Summary:        Tool to create and edit Inochi2D puppets

        '''.splitlines()]))

    # LICENSES

    # List direct licenses
    spec.write('\n'.join([
        "# Bundled lib licenses",
        ""]))        
    spec.write('\n'.join([
        "##   %s licenses: %s" % (
            lib.name, 
            ' and '.join(lib.licenses)
            ) for lib in session_project_libs]))
    spec.write('\n')

    # List static dependency licenses
    spec.write('\n'.join([
        "# Static dependencies licenses",
        ""]))        
    spec.write('\n'.join([
        "##   %s licenses: %s" % (
            lib.name, 
            ' and '.join(lib.licenses)
        ) for lib in session_indirect_libs]))
    spec.write('\n')

    # Add license field

    licenses = list(set().union(
        *[lib.licenses for lib in session_project_libs],
        *[lib.licenses for lib in session_indirect_libs]))
    licenses.sort()
    licenses.remove("BSD-2-Clause")
    licenses.insert(0, "BSD-2-Clause")
    
    spec.write('\n'.join([
        "License:        %s" % ' and '.join(licenses),
        "",
        ""]))

    spec.write('\n'.join([line[8:] for line in '''\
        URL:            https://github.com/grillo-delmal/inochi-session-rpm

        #https://github.com/Inochi2D/inochi-session/archive/{inochi_session_commit}/{name}-{inochi_session_short}.tar.gz
        Source0:        %{name}-%{version}-norestricted.tar.gz
        Source1:        inochi-session.appdata.xml
        Source2:        icon.png
        Source3:        config.d
        Source4:        banner.png
        Source5:        generate-tarball.sh
        Source6:        README.md
    
        '''.splitlines()]))

    # OTHER SOURCES
    spec.write('\n'.join([
        "# Project maintained deps",
        ""]))        

    src_cnt = 7

    for lib in session_project_libs:
        spec.write('\n'.join([
            "Source%d:%s%s" % (
                src_cnt, 
                " " * (8 - math.floor(math.log10(src_cnt) if src_cnt > 0 else 0)), 
                lib.source) ,
            ""
        ]))
        src_cnt += 1
    spec.write('\n')

    # PATCHES
    ptch_cnt = 0

    patch_list = []
    if Path("patches/%s" % "inochi-session").exists():
        patch_list = list(Path("patches/%s" % "inochi-session").glob("*.patch"))
        patch_list.sort()
    for file in patch_list:
        spec.write('\n'.join([
            "Patch%d:%s%s" % (
                ptch_cnt, 
                " " * (9 - math.floor(math.log10(ptch_cnt) if ptch_cnt > 0 else 0)), 
                file.name) ,
            ""
        ]))
        ptch_cnt += 1

    # OTHER PATCHES
    for lib in session_project_libs:
        for patch in lib.patches:
            spec.write('\n'.join([
                "Patch%d:%s%s" % (
                    ptch_cnt, 
                    " " * (9 - math.floor(math.log10(ptch_cnt) if ptch_cnt > 0 else 0)), 
                    patch) ,
                ""
            ]))
            ptch_cnt += 1
    spec.write('\n')
    spec.write('\n')

    # DEPS

    spec.write('\n'.join([line[8:] for line in '''\
        # dlang
        BuildRequires:  ldc
        BuildRequires:  dub

        BuildRequires:  desktop-file-utils
        BuildRequires:  libappstream-glib
        BuildRequires:  git

        '''.splitlines()]))

    spec.write('\n'.join([
        "BuildRequires:  zdub-%s-static" % lib.name \
            for lib in session_indirect_libs]))
    spec.write('\n')
    spec.write('\n')

    spec.write('\n'.join([line[8:] for line in '''\
        Requires:       luajit
        Requires:       hicolor-icon-theme


        '''.splitlines()]))

    spec.write('\n'.join([line[8:] for line in '''\
        %description
        Inochi2D is a framework for realtime 2D puppet animation which can be used for VTubing, 
        game development and digital animation. 
        Inochi Session is a tool that lets you use Inochi2D puppets as tracked avatars.
        This is an unbranded build, unsupported by the official project.

        '''.splitlines()]))

    # PREP

    spec.write('\n'.join([line[8:] for line in '''\
        %prep
        %setup -n %{name}-%{inochi_session_commit}

        '''.splitlines()]))

    # GENERIC FIXES
    spec.write('\n'.join([line[8:] for line in '''\
        # FIX: Inochi session version dependent on git
        cat > source/session/ver.d <<EOF
        module session.ver;

        enum INC_VERSION = "%{inochi_session_semver}";
        EOF

        # FIX: Replace config.d and banner.png
        rm source/session/config.d
        cp %{SOURCE3} source/session/
        cp %{SOURCE4} res/ui/banner.png

        '''.splitlines()]))

    src_cnt = 7
    ptch_cnt = 0

    patch_list = []
    if Path("patches/%s" % "inochi-session").exists():
        patch_list = list(Path("patches/%s" % "inochi-session").glob("*.patch"))
        patch_list.sort()
    for file in patch_list:
        spec.write('\n'.join([
            "%%patch -P %d -p1 -b .%s-%s" % (
                ptch_cnt,
                *list(file.name[:-6].split("_")[0::2])),
            ""
        ]))
        ptch_cnt += 1

    # PREP DEPS
    spec.write('\n'.join([line[8:] for line in '''\
        mkdir deps

        # Project maintained deps
        '''.splitlines()]))

    for lib in session_project_libs:
        spec.write('\n'.join([
            "tar -xzf %%{SOURCE%d}" % src_cnt,
            "mv %s deps/%s" % (
                lib.prep_file, lib.name), 
            "dub add-local deps/%s/ \"%%{%s_semver}\"" % (
                lib.name, lib.name.replace('-', '_').lower()),
            ""
        ]))

        if len(lib.patches) > 0 or len(lib.prep) > 0:
            spec.write('\n')
            spec.write('\n'.join([
                "pushd deps; pushd %s" % lib.name,
                ""
                ]))
            if len(lib.patches) > 0:
                spec.write('\n')
                for patch in lib.patches:
                    spec.write('\n'.join([
                        "%%patch -P %d -p1 -b .%s-%s" % (
                            ptch_cnt,
                            *list(patch[:-6].split("_")[0::2])),
                        ""
                    ]))
                    ptch_cnt += 1

            if len(lib.prep) > 0:
                spec.write('\n')
                spec.write('\n'.join(lib.prep))

            spec.write('\n'.join([
                "",
                "popd; popd",
                ""
                ]))

        spec.write('\n')
        src_cnt += 1

    spec.write('\n')

    # BUILD
    spec.write('\n'.join([line[8:] for line in '''\
        %build
        export DFLAGS="%{_d_optflags}"
        dub build \\
            --cache=local \\
            --config=barebones \\
            --skip-registry=all \\
            --temp-build \\
            --compiler=ldc2
        mkdir ./out/
        cp /tmp/.dub/build/inochi-session*/barebones*/* ./out/


        '''.splitlines()]))

    # INSTALL

    spec.write('\n'.join([line[8:] for line in '''\
        %install
        install -d ${RPM_BUILD_ROOT}%{_bindir}
        install -p ./out/inochi-session ${RPM_BUILD_ROOT}%{_bindir}/inochi-session

        install -d ${RPM_BUILD_ROOT}%{_datadir}/applications/
        install -p -m 644 res/inochi-session.desktop ${RPM_BUILD_ROOT}%{_datadir}/applications/inochi-session.desktop
        desktop-file-validate \\
            ${RPM_BUILD_ROOT}%{_datadir}/applications/inochi-session.desktop

        install -d ${RPM_BUILD_ROOT}%{_metainfodir}/
        install -p -m 644 %{SOURCE1} ${RPM_BUILD_ROOT}%{_metainfodir}/inochi-session.appdata.xml
        appstream-util validate-relax --nonet \\
            ${RPM_BUILD_ROOT}%{_metainfodir}/inochi-session.appdata.xml

        install -d $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/256x256/apps/
        install -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/256x256/apps/inochi-session.png

        '''.splitlines()]))
    
    # INSTALL LICENSES
    spec.write('\n'.join([line[8:] for line in '''\
        # Dependency licenses
        install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/deps/
        find ./deps/ -mindepth 1 -maxdepth 1 -exec \\
            install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/{} ';'

        find ./deps/ -mindepth 2 -maxdepth 2 -iname '*LICENSE*' -exec \\
            install -p -m 644 "{}" "${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/{}" ';'

        install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/res/
        find ./res/ -mindepth 1 -maxdepth 1 -iname '*LICENSE*' -exec \\
            install -p -m 644 {} ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/{} ';'


        '''.splitlines()]))

    # FILES
    spec.write('\n'.join([line[8:] for line in '''\
        %files
        %license LICENSE
        %{_datadir}/licenses/%{name}/*
        %{_bindir}/inochi-session
        %{_metainfodir}/inochi-session.appdata.xml
        %{_datadir}/applications/inochi-session.desktop
        %{_datadir}/icons/hicolor/256x256/apps/inochi-session.png


        %changelog
        %autochangelog
        '''.splitlines()][:-1]))

