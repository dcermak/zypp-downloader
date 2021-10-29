# zypp-downloader

`zypp-downloader` is a tiny shell script that downloads the recursive
dependencies of a list of packages from the repositories of your current system
via `zypper`.

It is intended to fetch rpms inside a container with zypper installed and copy
them into a second stage container with only rpm present:

```Dockerfile
FROM registry.opensuse.org/opensuse/tumbleweed:latest as builder
RUN zypper -n in curl && \
    curl https://raw.githubusercontent.com/dcermak/zypp-downloader/main/zypp-downloader  > /bin/zypp-downloader && \
    chmod +x /bin/zypp-downloader
RUN zypp-downloader find && \
    for pkg in /var/cache/rpms/*; do if rpm -qa|grep -q $(basename ${pkg//\.rpm/}); then rm $pkg; fi; done

FROM registry.opensuse.org/opensuse/tumbleweed:latest
WORKDIR /tmp/
COPY --from=builder /var/cache/rpms/ .
RUN rpm -i *rpm && find /etc/ -name *release | grep -q /etc/os-release
```

## Usage

```ShellSession
$ zypp-downloader pkg1 pkg2 pkg3
```

The script will download all packages including their dependencies to
`/var/cache/rpms/` from where you can copy them into your next stage.


## Catches

- The script uses `zypper --disable-system-resolvables` to grab your
  dependencies, which can result in a different dependency resolution that what
  your current system or your target container has. E.g. on Tumbleweed you'll
  often get `busybox-coreutils` instead of `coreutils` or `libz-ng-compat1`
  instead of `libz1`.

- Some system packages self-conflict and rpm will then bail out if you try to
  install them via `rpm -i`.

- The script will fetch **all** dependencies of your package, including those
  already present on your system. You might not want to copy all of them into
  your target container.

Given the above constraints, you should consider removing some of the packages
that got downloaded. For instance to remove all packages from the cache that are
already installed, you can use the following snippet:
```bash
for pkg in /var/cache/rpms/*; do
    if rpm -qa|grep -q $(basename ${pkg//\.rpm/}); then
        rm $pkg
    fi
done
```
