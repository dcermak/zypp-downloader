import pytest
from pytest_container import  MultiStageBuild
from pytest_container import DerivedContainer


CONTAINERFILE = """WORKDIR /bin
COPY ./zypp-downloader .
"""

CONTAINERS = [
    DerivedContainer(base=base, containerfile=CONTAINERFILE)
    for base in (
        "registry.suse.com/suse/sle15:15.3",
        "registry.opensuse.org/opensuse/leap:15.3",
        "registry.opensuse.org/opensuse/leap:15.2",
        "registry.opensuse.org/opensuse/tumbleweed:latest",
    )
]


CONTAINERFILES = [
    f"""FROM $downloader as downloader
RUN zypp-downloader {pkgs}
RUN ls /var/cache/rpms/*rpm

FROM $downloader
WORKDIR /tmp/
COPY --from=downloader /var/cache/rpms .
RUN (rm libgcc* cracklib* libstdc++* busybox-coreutils* libz* || :) && rpm -i --force *rpm
RUN for pkg in {pkgs}; do rpm -q --whatprovides $$pkg; done
"""
    for pkgs in ("shadow", "gcc", "make python3-tk")
]


@pytest.mark.parametrize("container", CONTAINERS)
@pytest.mark.parametrize("containerfile", CONTAINERFILES)
def test_run_downloader(
    container_runtime, container, containerfile, tmp_path, pytestconfig
):
    build = MultiStageBuild(
        containers={"downloader": container}, containerfile_template=containerfile
    )
    build.build(tmp_path, pytestconfig, container_runtime)
