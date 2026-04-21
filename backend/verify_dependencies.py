#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificación de dependencias del proyecto
"""

print("\n" + "="*70)
print("🔍 VERIFICACIÓN DE IMPORTACIONES EN EL PROYECTO")
print("="*70 + "\n")

imports_status = []

# Test 1: Librerías base
tests = [
    ("FastAPI", lambda: __import__('fastapi')),
    ("SQLAlchemy", lambda: __import__('sqlalchemy')),
    ("Pandas", lambda: __import__('pandas')),
    ("Pydantic", lambda: __import__('pydantic')),
    ("Passlib", lambda: __import__('passlib')),
    ("Python-Jose", lambda: __import__('jose')),
    ("Bcrypt", lambda: __import__('bcrypt')),
    ("Python-dotenv", lambda: __import__('dotenv')),
    ("Uvicorn", lambda: __import__('uvicorn')),
    ("Alembic", lambda: __import__('alembic')),
    ("Cryptography", lambda: __import__('cryptography')),
]

for name, import_func in tests:
    try:
        import_func()
        print(f"✅ {name:<20} - INSTALADO")
    except ImportError as e:
        print(f"❌ {name:<20} - FALTA: {e}")
        imports_status.append(name)

# Test 2: Módulos del proyecto
print("\n" + "-"*70)
print("MÓDULOS DEL PROYECTO:\n")

modules = [
    ("app.core.security", "from app.core.security import hashear_contrasena, verificar_contrasena, crear_token_acceso, verificar_token"),
    ("app.services.analytics", "from app.services.analytics import MaintenanceAnalytics, ResumenAnalytica"),
    ("app.models.marca", "from app.models.marca import Marca"),
    ("app.models.equipo", "from app.models.equipo import Equipo, EstadoEquipo"),
    ("app.models.usuario", "from app.models.usuario import Usuario, TipoRol"),
    ("app.db.base_class", "from app.db.base_class import Base"),
    ("app.db.session", "from app.db.session import engine, SessionLocal, get_db"),
    ("app.main", "from app.main import app"),
]

for module_name, import_stmt in modules:
    try:
        exec(import_stmt)
        print(f"✅ {module_name:<30} - OK")
    except Exception as e:
        print(f"❌ {module_name:<30} - ERROR: {e}")
        imports_status.append(module_name)

print("\n" + "="*70)
if not imports_status:
    print("✅ TODAS LAS DEPENDENCIAS ESTÁN CORRECTAMENTE INSTALADAS")
else:
    print(f"⚠️  FALTANTES: {', '.join(imports_status)}")
print("="*70 + "\n")

