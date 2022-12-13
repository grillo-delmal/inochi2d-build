#!/usr/bin/python3

import json
import subprocess
import shutil

from pathlib import Path
from scripts.spec_gen import spec_gen

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

    spec_data = {}
    try:
        with open("spec_data/%s.json" % name) as f:
            spec_data = json.load(f)
    except FileNotFoundError:
        pass

    if Path("files/%s" % name).exists():
        spec_data = spec_data | {
            "file_sources": [
                {
                    "name": file.name, 
                    "path": str(file.relative_to("files/%s" % name).parent)} 
                for file in Path("files/%s" % name).glob("**/*") 
                if file.is_file()]}

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
        
    spec_gen(
        "build_out/zdub/zdub-%s/zdub-%s.spec" % (name, name),
        name, 
        SEMVER, 
        SEMVER, 
        0,
        "0000000", 
        list(
            { 
                dep.split(':')[0] 
                    for dep in list(id_deps)
            }),
        spec_data)

    indirect_build_reqs.append(
        "BuildRequires:  zdub-%s-static" % name)

indirect_build_reqs.append("")

# Write inochi-creator.spec

with open("build_out/inochi-creator.spec", 'w') as spec:

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
        "%%define inochi_creator_ver    %s" % GITVER,
        "%%define inochi_creator_semver %s" % SEMVER,
        "%%define inochi_creator_dist   %s" % GITDIST,
        "%%define inochi_creator_commit %s" % COMMIT,
        "%%define inochi_creator_short  %s" % COMMIT[:7],
        "",
        ""]))

    spec.write('\n'.join([
        '# Project maintained deps',
        "",
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
            "%%define %s_short  %s" % (NAME, COMMIT[:7]),
            "",
            ""]))

    spec.write('\n'.join([
        '# cimgui', 
        "",
        ""]))

    NAME = 'cimgui'
    GITPATH = './src/bindbc-imgui/deps/cimgui'
    COMMIT = subprocess.run(
        ['git', '-C', GITPATH, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    spec.write('\n'.join([
        "%%define %s_commit %s" % (NAME, COMMIT),
        "%%define %s_short  %s" % (NAME, COMMIT[:7]),
        ""]))

    NAME = 'imgui'
    GITPATH = './src/bindbc-imgui/deps/cimgui/imgui'
    COMMIT = subprocess.run(
        ['git', '-C', GITPATH, 'rev-parse', 'HEAD'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    spec.write('\n'.join([
        "%%define %s_commit %s" % (NAME, COMMIT),
        "%%define %s_short  %s" % (NAME, COMMIT[:7]),
        "",
        ""]))

    spec.write('\n'.join(indirect_build_reqs))
