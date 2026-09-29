"""Baseline coefficient models kept for calibrate.py --nathan and --nathan-re.

Not part of the JS port. flight.py holds only the shipped linear quad_model.
"""

import data
from flight import Aero


def nathan_model(p=None, name="nathan"):
    """Nathan's workbook forms (Anchor 7 Source 1) with optional multipliers."""
    p = data.NATHAN if p is None else p
    lo, hi = p["re_low"], p["re_high"]
    cdl, cdh, cds = p["cd_low_re"], p["cd_high_re"], p["cd_spin"]
    amp, ex = p["cl_amp"], p["cl_exp"]
    branch, lm, dm = p["re_branch"], p["lift_mult"], p["drag_mult"]

    def cd(spin, re):
        if not branch or re >= hi:
            cd0 = cdh
        elif re <= lo:
            cd0 = cdl
        else:
            cd0 = cdl + (cdh - cdl) * (re - lo) / (hi - lo)
        return (cd0 + cds * spin) * dm

    def cl(spin, re):
        return amp * spin**ex * lm

    return Aero(name, cd, cl)
