import reflex as rx
from reflex.plugins import RadixThemesPlugin, SitemapPlugin

config = rx.Config(
    app_name="tanstack_charts_demo",
    # The gallery uses rx.card/heading/badge/... (Radix Themes). Declaring it
    # explicitly avoids implicit enabling, deprecated in Reflex 0.9 and removed in 1.0.
    plugins=[RadixThemesPlugin()],
    # Local single-page demo (REQ-CH-021), with no SEO use: the plugin enabled by
    # default is disabled instead of being inherited implicitly.
    disable_plugins=[SitemapPlugin],
)
