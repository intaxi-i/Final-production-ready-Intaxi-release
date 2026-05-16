"""FastAPI backend package for InTaxi mini app."""

from api.country_bootstrap import apply_country_config
from api.intaxi_production_patch import install_intaxi_production_patch

apply_country_config()
install_intaxi_production_patch()

__all__ = ["__version__"]

__version__ = "0.1.0"
