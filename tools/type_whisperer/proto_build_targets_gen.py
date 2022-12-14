# Generate api/BUILD based on API type database. This contains target for v2, v3
# and all API protos. This is not the ideal way to be generating docs, see
# https://github.com/envoyproxy/envoy/issues/10311#issuecomment-603518498.

import re
import string
import sys

from tools.type_whisperer.api_type_db_pb2 import TypeDb

from google.protobuf import text_format

V2_REGEXES = list(
    map(
        re.compile, [
            r'envoy[\w\.]*\.(v1alpha\d?|v1)',
            r'envoy[\w\.]*\.(v2alpha\d?|v2)',
            r'envoy\.type\.matcher$',
            r'envoy\.type$',
            r'envoy\.config\.cluster\.redis',
            r'envoy\.config\.retry\.previous_priorities',
        ]))

V3_REGEX = re.compile(r'envoy[\w\.]*\.(v3alpha|v3)')

# We didn't upgrade these as v2/v3 were the same, but later on decided that
# we would upgrade. We need to preseve both v2/v3 variants for now in the v3
# API.
ACCIDENTAL_V3_PKGS = [
    'envoy.config.filter.thrift.router.v2alpha1',
    'envoy.config.health_checker.redis.v2',
    'envoy.config.resource_monitor.fixed_heap.v2alpha',
    'envoy.config.resource_monitor.injected_resource.v2alpha',
    'envoy.config.retry.omit_canary_hosts.v2',
    'envoy.config.retry.previous_hosts.v2',
]

API_BUILD_FILE_TEMPLATE = string.Template(
    """# DO NOT EDIT. This file is generated by tools/proto_format/proto_sync.py.

load("@rules_proto//proto:defs.bzl", "proto_descriptor_set", "proto_library")

licenses(["notice"])  # Apache 2

proto_library(
    name = "v2_protos",
    visibility = ["//visibility:public"],
    deps = [
$v2_deps
    ],
)

proto_library(
    name = "v3_protos",
    visibility = ["//visibility:public"],
    deps = [
$v3_deps
    ],
)

proto_library(
    name = "xds_protos",
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_cncf_udpa//xds/core/v3:pkg",
        "@com_github_cncf_udpa//xds/type/matcher/v3:pkg",
        "@com_github_cncf_udpa//xds/type/v3:pkg",
    ],
)

proto_library(
    name = "all_protos",
    visibility = ["//visibility:public"],
    deps = [
        ":v2_protos",
        ":v3_protos",
        ":xds_protos",
    ],
)

filegroup(
    name = "proto_breaking_change_detector_buf_config",
    srcs = [
        "buf.yaml",
    ],
    visibility = ["//visibility:public"],
)

proto_descriptor_set(
    name = "v3_proto_set",
    visibility = ["//visibility:public"],
    deps = [
        ":v3_protos",
        ":xds_protos",
    ],
)
""")


def load_type_db(type_db_path):
    type_db = TypeDb()
    with open(type_db_path, 'r') as f:
        text_format.Merge(f.read(), type_db)
    return type_db


# Key sort function to achieve consistent results with buildifier.
def build_order_key(key):
    return key.replace(':', '!')


# Remove any packages that are definitely non-root, e.g. annotations.
def filter_pkgs(pkgs):

    def allowed_pkg(pkg):
        return not pkg.startswith('envoy.annotations')

    return filter(allowed_pkg, pkgs)


def deps_format(pkgs):
    return '\n'.join(
        f"""        "//{p.replace('.', '/')}:pkg","""
        for p in sorted(filter_pkgs(pkgs), key=build_order_key)
    )


def is_v2_package(pkg):
    return any(regex.match(pkg) for regex in V2_REGEXES)


def accidental_v3_package(pkg):
    return pkg in ACCIDENTAL_V3_PKGS


def is_v3_package(pkg):
    return V3_REGEX.match(pkg) is not None


if __name__ == '__main__':
    type_db_path, output_path = sys.argv[1:]
    type_db = load_type_db(type_db_path)
    # TODO(htuch): generalize to > 2 versions
    v2_packages = set([])
    v3_packages = set([])
    for desc in type_db.types.values():
        pkg = desc.qualified_package
        if is_v3_package(pkg):
            # contrib API files have the standard namespace but are in a contrib folder for clarity.
            # The following prepends contrib to the package path which indirectly will produce the
            # proper bazel path.
            if desc.proto_path.startswith('contrib/'):
                pkg = f"contrib.{pkg}"
            v3_packages.add(pkg)
            continue
        if is_v2_package(pkg):
            v2_packages.add(pkg)
            # Special case for v2 packages that are part of v3 (still active)
            if accidental_v3_package(pkg):
                v3_packages.add(pkg)
    # Generate BUILD file.
    build_file_contents = API_BUILD_FILE_TEMPLATE.substitute(
        v2_deps=deps_format(v2_packages), v3_deps=deps_format(v3_packages))
    with open(output_path, 'w') as f:
        f.write(build_file_contents)
