import reflex as rx
from reflex.plugins import RadixThemesPlugin, SitemapPlugin

config = rx.Config(
    app_name="tanstack_charts_demo",
    # La galería usa rx.card/heading/badge/... (Radix Themes). Declararlo explícito
    # evita la habilitación implícita, deprecada en Reflex 0.9 y eliminada en 1.0.
    plugins=[RadixThemesPlugin()],
    # Demo local de una sola página (REQ-CH-021), sin uso SEO: se desactiva el
    # plugin habilitado por defecto en vez de heredarlo implícitamente.
    disable_plugins=[SitemapPlugin],
)
