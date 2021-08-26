from typing import List
from ..event import MemberPerm
# from ..message import Group as GraiaGroup


class ExecClass:
    Name: str
    Target: object
    # Group: List[GraiaGroup]
    Group: List[int]
    Permission: List[MemberPerm]
    At: bool
    Shell_like: bool

    def __init__(
        self,
        name: str,
        target: object,
        group: List[int] = None,
        permission: MemberPerm = None,
        at: bool = False,
        shell_like: bool = False
    ):
        self.Name = name
        self.Target = target
        self.Group = group or []
        self.Permission = permission or []
        self.At = at
        self.Shell_like = shell_like

    def _check_perm(self):
        pass

    def __repr__(self):
        return f'<Command, name={self.Name.__repr__()}>'

    def __str__(self):
        return self.__repr__()
