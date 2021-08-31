from typing import List

from graia.application.entry import MemberPerm
# from graia.application.entry import Group as GraiaGroup


class ExecClass:
    Name: str
    Target: object
    # Group: List[GraiaGroup]
    Group: List[int]
    Permission: List[MemberPerm]
    At: bool
    Shell_like: bool
    Is_alias: bool
    Desc: str

    def __init__(
            self,
            name: str,
            desc: str,
            target: object,
            group: List[int] = None,
            permission: MemberPerm = None,
            at: bool = False,
            shell_like: bool = True,
            is_alias: bool = False
    ):
        self.Name = name
        self.Desc = desc
        self.Target = target
        self.Group = group or []
        self.Permission = permission or []
        self.At = at
        self.Shell_like = shell_like
        self.Is_alias = is_alias

    def _check_perm(self):
        pass

    def __repr__(self):
        return f'<Command, name={self.Name.__repr__()}>'

    def __str__(self):
        return self.__repr__()
