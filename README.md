# NOVA Trading AI — Updates

Repositorio de actualizaciones automáticas para NOVA Dashboard.

## Estructura

```
releases/
├── version_manifest.json    ← El cliente descarga esto primero
└── files/                   ← Solo los archivos que cambiaron
    ├── nova_dashboard.py
    ├── nova_diagnostics.py
    ├── nova_updater.py
    ├── services/
    │   ├── telemetry_service.py
    │   └── ...
    └── pares/
        ├── eurusd/
        └── ...
```

## Cómo publicar una actualización

```bash
# 1. Generar manifest con los archivos actualizados
python generate_manifest.py --version 5.1.0

# 2. Subir a GitHub
git add releases/
git commit -m "release: v5.1.0"
git push origin main
```

Los clientes ven el banner de actualización automáticamente.
