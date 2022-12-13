#!/usr/bin/python3

import json
import subprocess
from pathlib import Path
from spec_gen import spec_gen
import shutil

f = open("build_out/describe")

data = json.load(f)

dep_graph = {
    package['name']: package 
        for package in data['packages'] }

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

print("%define inochi_creator_ver", GITVER)
print("%define inochi_creator_semver", SEMVER)
print("%define inochi_creator_dist", GITDIST)
print("%define inochi_creator_commit", COMMIT)
print("%define inochi_creator_short", COMMIT[:7])
print()

def find_deps(parent, dep_graph):
    deps = set(dep_graph[parent]['dependencies'])
    for name in dep_graph[parent]['dependencies']:
        deps = deps.union(find_deps(name, dep_graph))
    return deps

deps = list(find_deps("inochi-creator", dep_graph))
deps.sort()

#print('# Project maintained deps')
project_deps = {
    name: dep_graph[name] 
        for name in dep_graph.keys() 
        if not dep_graph[name]['path'].startswith(
            '/opt/src/inochi-creator') and \
        name in deps}

pd_names = list(project_deps.keys())
pd_names.sort()

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

    Path("build_out/zdub/zdub-%s"  % name).mkdir(parents=True, exist_ok=True)

    for file in Path("files/%s" % name).glob("**/*"):
        if file.is_file():
            shutil.copy(file, "build_out/zdub/zdub-%s/" % name)

    for file in Path("patches/%s" % name).glob("*.patch"):
        shutil.copy(file, "build_out/zdub/zdub-%s/" % name)

    spec_data = {}
    try:
        with open("spec_data/%s.json" % name) as f:
            spec_data = json.load(f)
    except FileNotFoundError:
        pass
    
    if Path("patches/%s" % name).exists():
        spec_data = spec_data | {
            "patches": [
                file.name 
                for file in Path("patches/%s" % name).glob("*.patch")]}

    if Path("files/%s" % name).exists():
        spec_data = spec_data | {
            "file_sources": [
                {
                    "name": file.name, 
                    "path": str(file.relative_to("files/%s" % name).parent)} 
                for file in Path("files/%s" % name).glob("**/*") 
                if file.is_file()]}

    if name == "bindbc-imgui":
        # add imgui deps

        NAME = 'cimgui'
        CIMGUI_GITPATH = './src/bindbc-imgui/deps/cimgui'
        CIMGUI_COMMIT = subprocess.run(
            ['git', '-C', CIMGUI_GITPATH, 'rev-parse', 'HEAD'],
            stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

        NAME = 'imgui'
        IMGUI_GITPATH = './src/bindbc-imgui/deps/cimgui/imgui'
        IMGUI_COMMIT = subprocess.run(
            ['git', '-C', IMGUI_GITPATH, 'rev-parse', 'HEAD'],
            stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

        spec_data = spec_data | {
            "vars": {
                "cimgui_commit": CIMGUI_COMMIT,
                "cimgui_short": CIMGUI_COMMIT[:7],
                "imgui_commit": IMGUI_COMMIT,
                "imgui_short": IMGUI_COMMIT[:7]
            },
            "sources" : [
                "https://github.com/Inochi2D/bindbc-imgui/archive/%{lib_commit}/bindbc-imgui-%{lib_short}.tar.gz",
                "https://github.com/Inochi2D/cimgui/archive/%{cimgui_commit}/cimgui-%{cimgui_short}.tar.gz",
                "https://github.com/Inochi2D/imgui/archive/%{imgui_commit}/imgui-%{imgui_short}.tar.gz"
            ]
        }

    spec_gen(
        "build_out/zdub/zdub-%s/zdub-%s.spec" % (name, name),
        name, 
        GITVER, 
        SEMVER, 
        GITDIST,
        COMMIT, 
        project_deps[name]['dependencies'],
        spec_data)

#print('# Indirect deps')
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
        list(id_deps),
        spec_data)

