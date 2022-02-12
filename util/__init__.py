#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def get_graia_version():
    from importlib import metadata

    official: list[tuple[str, str]] = []
    community: list[tuple[str, str]] = []

    for dist in metadata.distributions():
        name: str = dist.metadata['Name']
        version: str = dist.version
        if name.startswith('graia-'):
            official.append((' '.join(name.split('-')[1:]).title(), version))
        elif name.startswith('graiax-'):
            community.append((' '.join(name.split('-')).title(), version))

    return official, community
