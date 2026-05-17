"""FastAPI backend package for InTaxi mini app."""

from api.country_bootstrap import apply_country_config
from api.intaxi_accept_patch import install_intaxi_accept_patch
from api.intaxi_intercity_patch import install_intaxi_intercity_patch
from api.intaxi_intercity_status_patch import install_intaxi_intercity_status_patch
from api.intaxi_production_patch import install_intaxi_production_patch
from api.intaxi_router_patch import install_router_route_patch
from api.intaxi_safety_patch import install_intaxi_safety_patch
from api.intaxi_terminal_patch import install_intaxi_terminal_patch

apply_country_config()
install_router_route_patch()
install_intaxi_production_patch()
install_intaxi_safety_patch()
install_intaxi_accept_patch()
install_intaxi_intercity_patch()
install_intaxi_intercity_status_patch()
install_intaxi_terminal_patch()

__all__ = ["__version__"]

__version__ = "0.1.0"
