from typing import List
from ..event import MemberPerm
from ..message import Group


class ExecClass:
    Target: object
    Group: List[Group.id]
    Permission: List[MemberPerm]
    At: bool
    Shell_like: bool

    def __init__(
        self,
        target: object,
        group: List[int] = None,
        permission: MemberPerm = None,
        at: bool = False,
        shell_like: bool = False
    ):
        self.Target = target
        self.Group = group or []
        self.Permission = permission or []
        self.At = at
        self.Shell_like = shell_like

    def _check_perm(self):
        pass

    def __repr__(self):
        return f'<Command, name={self.name.__repr__()}>'

    def __str__(self):
        return self.__repr__()
