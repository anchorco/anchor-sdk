"""Default policy configurations for Anchor agents."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DefaultPolicyPack:
    """
    Production ready default policies for agent config.

    Usage:
        from anchor import DefaultPolicyPack

        # Apply defaults
        anchor.config.update(agent.id, DefaultPolicyPack().get_config())

        # Customize defaults
        pack = DefaultPolicyPack(
            block_secrets=False,
            max_query_size=None  # Disable specific policy
        )
        anchor.config.update(agent.id, pack.get_config())
    """

    allowed_domains: Optional[list[str]] = None
    max_query_size: Optional[int] = 1000
    require_approval_for: Optional[list[str]] = field(
        default_factory=lambda: ["delete", "update", "export"]
    )
    block_pii: bool = True
    block_secrets: bool = True

    def get_config(self) -> dict[str, Any]:
        """
        Returns dict with configured policies to be used in `config`
        """
        policies: dict[str, Any] = {}

        if self.allowed_domains is not None:
            policies["allowed_domains"] = self.allowed_domains

        if self.max_query_size is not None:
            policies["max_query_size"] = self.max_query_size

        if self.require_approval_for is not None:
            policies["require_approval_for"] = self.require_approval_for

        policies["block_pii"] = self.block_pii
        policies["block_secrets"] = self.block_secrets

        return {"policies": policies}
