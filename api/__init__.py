"""FastAPI backend package for InTaxi mini app."""

from api.intaxi_production_patch import install_intaxi_production_patch

install_intaxi_production_patch()

__all__ = ["__version__"]

__version__ = "0.1.0"
