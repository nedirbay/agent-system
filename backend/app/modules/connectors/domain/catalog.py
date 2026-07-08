"""Catalogue of connectable external systems (MCP-style integrations).

The catalogue is the single source of truth for which third-party systems a user
can connect, and — crucially — which credential fields each one requires. The
presentation layer renders an "add" form from these field specs, and the
application layer validates submitted credentials against them.

Fields are split into:
  * config  — non-secret values, stored as-is (e.g. an email address, a chat id);
  * secret  — tokens / passwords, encrypted at rest and never returned to clients.

Adding a new integration is a data-only change here; no new code paths needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Field kinds drive the input type the UI renders.
FIELD_TEXT = "text"
FIELD_SECRET = "secret"


@dataclass(frozen=True)
class CredentialField:
    key: str
    label: str
    kind: str = FIELD_TEXT  # FIELD_TEXT | FIELD_SECRET
    required: bool = True
    placeholder: str = ""
    help: str = ""

    @property
    def is_secret(self) -> bool:
        return self.kind == FIELD_SECRET


@dataclass(frozen=True)
class ConnectorSpec:
    type: str
    name: str
    description: str
    category: str  # messaging | email | productivity | custom
    icon: str  # Element Plus icon name for the UI
    docs_url: str = ""
    fields: tuple[CredentialField, ...] = field(default_factory=tuple)

    @property
    def config_fields(self) -> tuple[CredentialField, ...]:
        return tuple(f for f in self.fields if not f.is_secret)

    @property
    def secret_fields(self) -> tuple[CredentialField, ...]:
        return tuple(f for f in self.fields if f.is_secret)


CONNECTOR_CATALOG: dict[str, ConnectorSpec] = {
    "slack": ConnectorSpec(
        type="slack",
        name="Slack",
        description="Post messages and read channels in your Slack workspace.",
        category="messaging",
        icon="ChatDotRound",
        docs_url="https://api.slack.com/apps",
        fields=(
            CredentialField(
                key="bot_token",
                label="Bot User OAuth Token",
                kind=FIELD_SECRET,
                placeholder="xoxb-…",
                help="Found under OAuth & Permissions in your Slack app settings.",
            ),
            CredentialField(
                key="default_channel",
                label="Default channel",
                kind=FIELD_TEXT,
                required=False,
                placeholder="#general",
                help="Optional channel agents post to when none is specified.",
            ),
        ),
    ),
    "gmail": ConnectorSpec(
        type="gmail",
        name="Gmail",
        description="Send email on your behalf through your Gmail account.",
        category="email",
        icon="Message",
        docs_url="https://support.google.com/accounts/answer/185833",
        fields=(
            CredentialField(
                key="email",
                label="Gmail address",
                kind=FIELD_TEXT,
                placeholder="you@gmail.com",
            ),
            CredentialField(
                key="app_password",
                label="App password",
                kind=FIELD_SECRET,
                placeholder="16-character app password",
                help="Create an app password with 2-Step Verification enabled.",
            ),
        ),
    ),
    "whatsapp": ConnectorSpec(
        type="whatsapp",
        name="WhatsApp Business",
        description="Send WhatsApp messages via the Meta WhatsApp Cloud API.",
        category="messaging",
        icon="ChatLineRound",
        docs_url="https://developers.facebook.com/docs/whatsapp/cloud-api",
        fields=(
            CredentialField(
                key="phone_number_id",
                label="Phone number ID",
                kind=FIELD_TEXT,
                placeholder="1234567890",
                help="From the WhatsApp > API Setup page in Meta for Developers.",
            ),
            CredentialField(
                key="access_token",
                label="Access token",
                kind=FIELD_SECRET,
                placeholder="EAAG…",
                help="A permanent or system-user token for the Cloud API.",
            ),
        ),
    ),
    "telegram": ConnectorSpec(
        type="telegram",
        name="Telegram",
        description="Send messages through a Telegram bot.",
        category="messaging",
        icon="Promotion",
        docs_url="https://core.telegram.org/bots#botfather",
        fields=(
            CredentialField(
                key="bot_token",
                label="Bot token",
                kind=FIELD_SECRET,
                placeholder="123456:ABC-DEF…",
                help="Issued by @BotFather when you create a bot.",
            ),
            CredentialField(
                key="default_chat_id",
                label="Default chat ID",
                kind=FIELD_TEXT,
                required=False,
                placeholder="@channel or numeric id",
            ),
        ),
    ),
    "mcp": ConnectorSpec(
        type="mcp",
        name="Custom MCP server",
        description="Connect any Model Context Protocol server over HTTP/SSE.",
        category="custom",
        icon="Connection",
        docs_url="https://modelcontextprotocol.io",
        fields=(
            CredentialField(
                key="endpoint",
                label="Server endpoint",
                kind=FIELD_TEXT,
                placeholder="https://my-mcp-server.example.com/sse",
            ),
            CredentialField(
                key="api_key",
                label="API key",
                kind=FIELD_SECRET,
                required=False,
                placeholder="optional",
                help="Leave blank for servers that don't require authentication.",
            ),
        ),
    ),
}


def get_connector_spec(connector_type: str) -> ConnectorSpec | None:
    return CONNECTOR_CATALOG.get(connector_type)
