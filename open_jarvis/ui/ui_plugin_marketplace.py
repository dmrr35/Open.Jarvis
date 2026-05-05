"""Plugin marketplace dialog for the JARVIS desktop UI."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from open_jarvis.plugins.plugin_marketplace import build_marketplace
from open_jarvis.ui.ui_theme import PALETTE, font

BG = PALETTE["bg"]
BG2 = PALETTE["bg_elevated"]
BLUE = PALETTE["cyan"]
BLUE_DIM = PALETTE["surface_soft"]
TEXT_DIM = PALETTE["text_muted"]
CARD = PALETTE["surface"]
LINE = PALETTE["line"]


def build_plugin_marketplace_text(root: Path | str = "plugins") -> str:
    """Render local plugin trust posture for the desktop marketplace dialog."""

    marketplace = build_marketplace(root)
    summary = marketplace["summary"]
    lines = [
        "Plugin Marketplace",
        f"Total: {summary['total']}  Trusted: {summary['trusted']}  Blocked: {summary['blocked']}",
        "",
    ]
    if not marketplace["plugins"]:
        lines.append("No local plugins were found.")
    for plugin in marketplace["plugins"]:
        lines.append(f"[{plugin['trust_status'].upper()}] {plugin['name']} {plugin['version']}")
        lines.append(f"  Signature: {plugin.get('signature_status', 'unknown')}")
        lines.append(f"  Sandbox: {plugin.get('sandbox_status', 'unknown')}")
        lines.append(f"  Enabled: {'yes' if plugin.get('enabled') else 'no'}")
        action = plugin.get("approval_action", {})
        if action:
            lines.append(f"  Approval action: {action.get('label', 'Review plugin')}")
        if plugin.get("description"):
            lines.append(f"  Description: {plugin['description']}")
        lines.append(f"  Path: {plugin['path']}")
        if plugin["issues"]:
            lines.append(f"  Issues: {', '.join(plugin['issues'])}")
        lines.append("")
    return "\n".join(lines).strip()


class PluginMarketplaceDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JARVIS Plugin Marketplace")
        self.geometry("1000x700")
        self.configure(fg_color=BG)
        self.grab_set()
        self._box = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="PLUGIN MARKETPLACE", font=font("display", 20, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=18, pady=(16, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="Local plugin trust status, signer validation, and blocked-plugin issues.",
            font=font("ui", 11),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, padx=18, pady=16, sticky="e")
        ctk.CTkButton(actions, text="Refresh", fg_color=BLUE_DIM, command=self._refresh).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Close", fg_color="#4a1f1f", command=self._close).pack(side="left", padx=4)

        body = ctk.CTkFrame(self, fg_color=CARD, corner_radius=28, border_width=1, border_color=LINE)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._box = ctk.CTkTextbox(body, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._box.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self._box.configure(state="disabled")

    def _refresh(self):
        self._box.configure(state="normal")
        self._box.delete("1.0", "end")
        self._box.insert("end", build_plugin_marketplace_text())
        self._box.configure(state="disabled")
        self._box.see("1.0")

    def _close(self):
        self.grab_release()
        self.destroy()
