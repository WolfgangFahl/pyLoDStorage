"""
Created on 2026-02-11

@author: wf
"""


class ActionStats:
    """
    track the success rate of actions, e.g. availability probes of endpoints
    """

    def __init__(self):
        self.success_count = 0
        self.total_count = 0
        self.current = None

    def add(self, is_success: bool):
        """
        add a single result

        Args:
            is_success: True if the action succeeded
        """
        self.current = is_success
        self.total_count += 1
        if is_success:
            self.success_count += 1

    @property
    def ratio(self) -> float:
        """
        the success/total ratio, 0.0 without results
        """
        ratio = self.success_count / self.total_count if self.total_count > 0 else 0.0
        return ratio

    def state(self, success_msg: str, fail_msg: str) -> str:
        """
        the current state as a marked message

        Args:
            success_msg: the message for a successful last action
            fail_msg: the message for a failed last action

        Returns:
            str: the marked message
        """
        if self.current:
            msg = f"✅{success_msg}"
        else:
            msg = f"❌: {fail_msg}"
        return msg

    def __str__(self) -> str:
        """
        the formatted summary
        """
        marker = "❌ " if self.success_count < self.total_count else "✅"
        text = f"{marker}:{self.success_count}/{self.total_count} available"
        return text
