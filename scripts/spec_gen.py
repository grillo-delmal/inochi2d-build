import math
import json
from pathlib import Path

def spec_get_data(name):
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
    return spec_data


def spec_gen(path, name, gitver, semver, dist, commit, deps):
    data = spec_get_data(name)

    with open(path, 'w') as f:

        # Macros

        f.write('\n'.join([
            "%global debug_package %{nil}",
            ""
        ]))
        if "macros" in data and len(data["macros"]) > 0:
            f.write('\n'.join(data["macros"]))

        # Variables

        f.write('\n'.join([
            "",
            "%%define lib_name      %s" % name,
            "%%define lib_ver       %s" % gitver.split("-")[0],
            "%%define lib_gitver    %s" % gitver,
            "%%define lib_semver    %s" % semver,
            "%%define lib_dist      %s" % dist,
            "%%define lib_commit    %s" % commit,
            "%%define lib_short     %s" % commit[:7],
            ""
        ]))
        if "vars" in data:
            for key in data["vars"].keys():
                f.write('\n'.join([
                    "%%define %s%s %s" % (
                        key,
                        " " * (13-len(key)),
                        data["vars"][key]) ,
                    ""
                ]))
        f.write('\n'.join([
            "",
            "%if 0%{lib_dist} > 0",
            "%define lib_suffix ^%{lib_dist}.git%{lib_short}",
            "%endif",
            "",
            ""
        ]))

        # General description

        f.write('\n'.join([
            "Name:           zdub-%{lib_name}",
            "Version:        %{lib_ver}%{?lib_suffix:}",
            "Release:        %autorelease",
            "Summary:        %s" % (data["summary"] if "summary" in data else "%{lib_name} library for D"),
            "Group:          Development/Libraries",
            "License:        %s" % (data["license"] if "license" in data else "BSD-2-Clause"),
            "URL:            %s" % (data["url"] if "url" in data else "https://github.com/Inochi2D/%{lib_name}"),
            ""
        ]))

        # Sources and patches

        if "sources" in data and len(data["sources"]) > 0:
            for i in range(len(data["sources"])):
                f.write('\n'.join([
                    "Source%d:%s%s" % (
                        i, 
                        " " * (8 - math.floor(math.log10(i) if i > 0 else 0)), 
                        data["sources"][i]) ,
                    ""
                ]))
        else:
            if int(dist) > 0:
                f.write('\n'.join([
                    "Source0:        https://github.com/Inochi2D/%{lib_name}"
                    "/archive/%{lib_commit}/%{lib_name}-%{lib_short}.tar.gz",
                    ""
                ]))
            else:
                f.write('\n'.join([
                    "Source0:        https://github.com/Inochi2D/%{lib_name}"
                    "/archive/v%{lib_gitver}/%{lib_name}-%{lib_gitver}.tar.gz",
                    ""
                ]))

        if "file_sources" in data and len(data["file_sources"]) > 0:
            src_cnt = len(data["sources"]) if "sources" in data and len(data["sources"]) else 1
            for i in range(len(data["file_sources"])):
                f.write('\n'.join([
                    "Source%d:%s%s" % (
                        src_cnt + i, 
                        " " * (8 - math.floor(math.log10(i) if i > 0 else 0)), 
                        data["file_sources"][i]["name"]) ,
                    ""
                ]))

        if "patches" in data and len(data["patches"]) > 0:
            f.write("\n")
            for i in range(len(data["patches"])):
                f.write('\n'.join([
                    "Patch%d:%s%s" % (
                        i, 
                        " " * (9 - math.floor(math.log10(i) if i > 0 else 0)), 
                        data["patches"][i]) ,
                    ""
                ]))
        f.write('\n')

        # Build Requirements

        f.write('\n'.join([
            "BuildRequires:  setgittag",
            "BuildRequires:  git",
            ""
        ]))
        if "build_reqs" in data and len(data["build_reqs"]) > 0:
            for build_req in data["build_reqs"]:
                f.write('\n'.join([
                    "BuildRequires:  %s" % build_req ,
                    ""
                ]))
        f.write('\n')
        f.write('\n')

        # Description

        f.write('\n'.join([
            "%description",
            ""
        ]))
        if "description" in data:
            f.write('\n'.join(data["description"]))
        else:
            f.write('\n'.join([
                "An actual description of %{lib_name}",
                "#FIXME: generate an actual description",
                ""
            ]))
        f.write('\n')
        f.write('\n')

        # Devel package info and requirements

        f.write('\n'.join([
            "%package devel",
            "Provides:       %{name}-static = %{version}-%{release}",
            "Summary:        Support to use %{lib_name} for developing D applications",
            "Group:          Development/Libraries",
            "",
            "Requires:       ldc",
            "Requires:       dub",
            "",
            "Requires:       zdub-dub-settings-hack",
            ""
        ]))
        if len(deps) > 0:
            for dep in deps:
                f.write("Requires:       zdub-%s-static\n" % dep)
        if "requires" in data:
            f.write('\n')
            for req in data["requires"]:
                f.write("Requires:       %s\n" % req)
        f.write('\n'.join([
            "",
            "",
            "%description devel",
            "Sources to use the %{lib_name} library on dub using the",
            "zdub-dub-settings-hack method.",
            ""
        ]))
        f.write('\n')
        f.write('\n')

        # Preparation

        f.write('\n'.join([
            "%prep",
            ""
        ]))
        if "prep_file" in data:
            f.write('\n'.join([
                "%%autosetup -n %s -p1" % data["prep_file"],
                ""
            ]))
        elif int(dist) > 0:
            f.write('\n'.join([
                "%autosetup -n %{lib_name}-%{lib_commit} -p1",
                ""
            ]))
        else:
            f.write('\n'.join([
                "%autosetup -n %{lib_name}-%{lib_gitver} -p1",
                ""
            ]))
        f.write('\n'.join([
            "setgittag --rm -f -m v%{lib_gitver}",
            ""
        ]))
        if "file_sources" in data and len(data["file_sources"]) > 0:
            f.write("\n")
            src_cnt = len(data["sources"]) if "sources" in data and len(data["sources"]) else 1
            for i in range(len(data["file_sources"])):
                if data["file_sources"][i]["path"] != ".":
                    f.write('\n'.join([
                        "mkdir -p ./%s" % data["file_sources"][i]["path"],
                        "cp --force %%{SOURCE%d} ./%s/" % (i + src_cnt, data["file_sources"][i]["path"]),
                        ""
                    ]))
                else:
                    f.write('\n'.join([
                        "cp %%{SOURCE%d} ." % (i + src_cnt),
                        ""
                    ]))
        if "prep" in data and len(data["prep"]) > 0:
            f.write("\n")
            f.write('\n'.join(data["prep"]))
        f.write('\n')
        f.write('\n')

        # Build data
        # TODO: Prebuild binaries in the future?

        f.write('\n'.join([
            "%build",
            "",
            "",
            ""
        ]))

        # Install data

        f.write('\n'.join([
            "%install",
            "mkdir -p %{buildroot}%{_includedir}/zdub/%{lib_name}-%{lib_gitver}",
            "cp -r "
                  ". "
                  "%{buildroot}%{_includedir}/zdub/%{lib_name}-%{lib_gitver}/%{lib_name}",
            ""
        ]))
        if "install" in data and len(data["install"]) > 0:
            f.write('\n'.join(data["install"]))
        f.write('\n')
        f.write('\n')

        # File list

        f.write('\n'.join([
            "%files devel",
            "%license LICENSE",
            "%{_includedir}/zdub/%{lib_name}-%{lib_gitver}/%{lib_name}/",
            ""
        ]))
        if "files" in data and len(data["files"]) > 0:
            f.write('\n'.join(data["files"]))
        f.write('\n'.join([
            "",
            "",
            "%changelog",
            "%autochangelog",
            ""
        ]))
