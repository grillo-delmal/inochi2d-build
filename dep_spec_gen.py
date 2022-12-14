#!/usr/bin/python3

import json
import subprocess
import shutil

from pathlib import Path
from scripts.spec_gen import LibSpecFile

data = {}
with open("build_out/describe") as f:
    data = json.load(f)

dep_graph = {
    package['name']: package 
        for package in data['packages'] }

def find_deps(parent, dep_graph):
    deps = set(dep_graph[parent]['dependencies'])
    for name in dep_graph[parent]['dependencies']:
        deps = deps.union(find_deps(name, dep_graph))
    return deps

deps = list(find_deps("inochi-creator", dep_graph))
deps.sort()

project_deps = {
    name: dep_graph[name] 
        for name in dep_graph.keys() 
        if not dep_graph[name]['path'].startswith(
            '/opt/src/inochi-creator') and \
        name in deps}

pd_names = list(project_deps.keys())
pd_names.sort()


# Write indirect deps spec files
indirect_build_reqs = []
indirect_deps = {
    name: dep_graph[name] 
        for name in dep_graph.keys() 
        if dep_graph[name]['path'].startswith(
            '/opt/src/inochi-creator') and \
        name in deps}

id_names = list(indirect_deps.keys())
id_names.sort()

true_deps = {}

for name in id_names:
    NAME = indirect_deps[name]['name'].lower()
    TRUENAME = NAME.split(":")[0]
    SEMVER = indirect_deps[name]['version']

    if TRUENAME in true_deps:
        true_deps[TRUENAME].append({"name": NAME, "semver":SEMVER})
    else:
        true_deps[TRUENAME] = [{"name": NAME, "semver":SEMVER}]

for name in true_deps:

    Path("build_out/zdub/zdub-%s"  % name).mkdir(parents=True, exist_ok=True)
    for file in Path("files/%s" % name).glob("**/*"):
        if file.is_file():
            shutil.copy(file, "build_out/zdub/zdub-%s/" % name)

    id_deps = set()
    SEMVER = true_deps[name][0]["semver"]

    for dep in true_deps[name]:
        id_deps = id_deps.union(set(dep_graph[dep["name"]]['dependencies']))
        SEMVER = dep["semver"]
        pass

    for dep in list(id_deps):
        dep_truename = dep.split(":")[0]
        if dep_truename != dep:
            id_deps.remove(dep)
            if dep_truename != name:
                id_deps.add(dep_truename)
        
    lib_spec = LibSpecFile(
        name, 
        list(
            { 
                dep.split(':')[0] 
                    for dep in list(id_deps)
            }), 
        SEMVER)

    lib_spec.spec_gen(
                "build_out/zdub/zdub-%s/zdub-%s.spec" % (name, name))

    indirect_build_reqs.append(
        "BuildRequires:  zdub-%s-static" % name)

indirect_build_reqs.append("")

# Write inochi-creator.spec

with open("build_out/inochi-creator.spec", 'w') as spec:

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

    spec.write('\n'.join([
        '# Project maintained deps',
        ""]))

    for name in pd_names:
        NAME = project_deps[name]['name'].replace('-', '_').lower()
        SEMVER = project_deps[name]['version']
        GITPATH = project_deps[name]['path'].replace("/opt","./")
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

        spec.write('\n'.join([
            "%%define %s_semver %s" % (NAME, SEMVER),
            "%%define %s_commit %s" % (NAME, COMMIT),
            "%%define %s_short %s" % (NAME, COMMIT[:7]),
            "",
            ""]))

    spec.write('\n'.join([
        '# cimgui', 
        ""]))

    NAME = 'cimgui'
    GITPATH = './src/bindbc-imgui/deps/cimgui'
    COMMIT = subprocess.run(
        ['git', '-C', GITPATH, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    spec.write('\n'.join([
        "%%define %s_commit %s" % (NAME, COMMIT),
        "%%define %s_short %s" % (NAME, COMMIT[:7]),
        ""]))

    NAME = 'imgui'
    GITPATH = './src/bindbc-imgui/deps/cimgui/imgui'
    COMMIT = subprocess.run(
        ['git', '-C', GITPATH, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    spec.write('\n'.join([
        "%%define %s_commit %s" % (NAME, COMMIT),
        "%%define %s_short %s" % (NAME, COMMIT[:7]),
        "",
        "",
        ""]))

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

    # TODO: ADD OTHER LICENSES
    spec.write('\n'.join([
        "License:        BSD2",
        "",
        ""]))

    spec.write('\n'.join([line[8:] for line in '''\
        URL:            https://github.com/grillo-delmal/inochi-creator-rpm

        #https://github.com/Inochi2D/inochi-creator/archive/{inochi_creator_commit}/{name}-{inochi_creator_short}.tar.gz
        Source0:        %{name}-%{version}-norestricted.tar.gz
        Source1:        inochi-creator.appdata.xml
        Source2:        icon.png
        Source3:        config.d
        Source4:        banner.png
        Source5:        generate-tarball.sh
        Source6:        README.md
    
        '''.splitlines()]))

    #TODO: OTHER SOURCES

    #TODO: PATCHES

    #TODO: OTHER PATCHES

    # DEPS

    spec.write('\n'.join(indirect_build_reqs))

    spec.write('\n'.join([line[8:] for line in '''\
        # dlang
        BuildRequires:  ldc
        BuildRequires:  dub

        # cimgui
        BuildRequires:  cmake
        BuildRequires:  gcc
        BuildRequires:  gcc-c++
        BuildRequires:  freetype-devel
        BuildRequires:  SDL2-devel
        BuildRequires:  dbus-devel

        BuildRequires:  desktop-file-utils
        BuildRequires:  libappstream-glib
        BuildRequires:  git

        '''.splitlines()]))

    spec.write('\n'.join(indirect_build_reqs))

    spec.write('\n'.join([line[8:] for line in '''\

        Requires:       hicolor-icon-theme


        '''.splitlines()]))

    spec.write('\n'.join([line[8:] for line in '''\
        %description
        Inochi2D is a framework for realtime 2D puppet animation which can be used for VTubing, 
        game development and digital animation. 
        Inochi Creator is a tool that lets you create and edit Inochi2D puppets.
        This is an unbranded build, unsupported by the official project.

        '''.splitlines()]))

    #TODO: PREP

    spec.write('\n'.join([line[8:] for line in '''\
        %prep
        %setup -n %{name}-%{inochi_creator_commit}

        '''.splitlines()]))

    #TODO: GENERIC PATCHES
    spec.write('\n'.join([line[8:] for line in '''\
        %patch0 -p1 -b .icon-fix

        # FIX: Inochi creator version dependent on git
        %patch1 -p1 -b .no-gitver-a
        cat > source/creator/ver.d <<EOF
        module creator.ver;

        enum INC_VERSION = "%{inochi_creator_semver}";
        EOF

        '''.splitlines()]))

    #TODO: GENERIC FIXES
    spec.write('\n'.join([line[8:] for line in '''\
        # FIX: Replace config.d and banner.png
        rm source/creator/config.d
        cp %{SOURCE3} source/creator/
        cp %{SOURCE4} res/ui/banner.png

        '''.splitlines()]))

    #TODO: PREP DEPS
    spec.write('\n'.join([line[8:] for line in '''\
        mkdir deps

        # Project maintained deps
        '''.splitlines()]))

    spec.write('\n'.join([line[8:] for line in '''\


        '''.splitlines()]))

    # BUILD
    spec.write('\n'.join([line[8:] for line in '''\
        %build
        export DFLAGS="%{_d_optflags}"
        dub build \\
            --cache=local \\
            --config=barebones \\
            --skip-registry=all \\
            --compiler=ldc2


        '''.splitlines()]))

    # INSTALL

    spec.write('\n'.join([line[8:] for line in '''\
        %install
        install -d ${RPM_BUILD_ROOT}%{_bindir}
        install -p ./out/inochi-creator ${RPM_BUILD_ROOT}%{_bindir}/inochi-creator

        install -d ${RPM_BUILD_ROOT}%{_datadir}/applications/
        install -p -m 644 res/inochi-creator.desktop ${RPM_BUILD_ROOT}%{_datadir}/applications/inochi-creator.desktop
        desktop-file-validate \\
            ${RPM_BUILD_ROOT}%{_datadir}/applications/inochi-creator.desktop

        install -d ${RPM_BUILD_ROOT}%{_metainfodir}/
        install -p -m 644 %{SOURCE1} ${RPM_BUILD_ROOT}%{_metainfodir}/inochi-creator.appdata.xml
        appstream-util validate-relax --nonet \\
            ${RPM_BUILD_ROOT}%{_metainfodir}/inochi-creator.appdata.xml

        install -d $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/256x256/apps/
        install -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/256x256/apps/inochi-creator.png

        '''.splitlines()]))
    
    # INSTALL LICENSES
    spec.write('\n'.join([line[8:] for line in '''\
        # Dependency licenses
        install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/./deps/bindbc-imgui/cimgui/
        install -p -m 644 ./deps/bindbc-imgui/deps/cimgui/LICENSE \\
            ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/./deps/bindbc-imgui/cimgui/LICENSE
        install -d ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/./deps/bindbc-imgui/imgui/
        install -p -m 644 ./deps/bindbc-imgui/deps/cimgui/imgui/LICENSE.txt \\
            ${RPM_BUILD_ROOT}%{_datadir}/licenses/%{name}/./deps/bindbc-imgui/imgui/LICENSE.txt

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
