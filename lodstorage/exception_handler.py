"""
Created on 2025-12-01

@author: wf
"""
import logging
import traceback


class ExceptionHandler:
    """
    handle exceptions
    """

    @classmethod
    def handle(
        cls, msg: str, ex: Exception, debug: bool = False
    ):
        """Centralized exception logging (non-fatal).

        Args:
            msg: context message
            ex: the exception caught
            debug: if True, print full traceback
        """
        full_msg = f"{msg}: {str(ex)}"
        logging.warning(full_msg)
        if debug:
            traceback.print_exc()