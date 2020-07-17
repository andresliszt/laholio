"""Inicialización para laholio."""

from petri import Petri

pkg = Petri(__file__)  # pylint: disable=invalid-name
S = pkg.settings
DATA_DIR = S.DATA

__meta__ = pkg.meta.data


logger = pkg.log  # pylint: disable=invalid-name

logger.debug("initialized laholio", **dict(S))
