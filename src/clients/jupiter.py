from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class JupiterClient:
    """
    Jupiter DEX client interface.
    Implements methods for interacting with Jupiter DEX for token swaps.
    """

    def __init__(self, rpc_endpoint: str, auth_token: str):
        self.rpc_endpoint = rpc_endpoint
        self.auth_token = auth_token
        logger.info(
            f"Initialized Jupiter client with endpoint: {rpc_endpoint}")

    async def get_quote(
        self,
        input_token: str,
        output_token: str,
        amount: float,
        side: str
    ) -> Dict[str, Any]:
        """Get a quote for swapping tokens."""
        raise NotImplementedError

    async def execute_swap(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a token swap based on the provided quote."""
        raise NotImplementedError

    async def get_token_info(self, token: str) -> Dict[str, Any]:
        """Get information about a token."""
        raise NotImplementedError
