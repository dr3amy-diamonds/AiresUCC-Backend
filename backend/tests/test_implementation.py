"""
ARCHIVO DE PRUEBAS - Validación de los 5 módulos
==================================================

Este script permite validar que todos los módulos se importan correctamente
y que las funcionalidades básicas funcionan como se espera.

Para ejecutar:
    cd backend
    python -m pytest ../tests/test_implementation.py -v

O para pruebas manuales:
    python << 'EOF'
    # Copiar el contenido de test_manual() abajo
    EOF
"""

import sys
from datetime import timedelta
from typing import List, Dict

# =============================================================================
# TEST 1: VALIDAR IMPORTS DE MODELOS
# =============================================================================
def test_imports_modelos():
    """Verifica que los modelos se pueden importar correctamente."""
    print("\n🔍 TEST 1: Importando modelos...")
    try:
        from app.models import Marca, Equipo, Usuario, EstadoEquipo, TipoRol
        print("✅ Modelos importados exitosamente")
        print(f"   - Marca: {Marca}")
        print(f"   - Equipo: {Equipo}")
        print(f"   - Usuario: {Usuario}")
        print(f"   - EstadoEquipo: {EstadoEquipo}")
        print(f"   - TipoRol: {TipoRol}")
        return True
    except Exception as e:
        print(f"❌ Error importando modelos: {e}")
        return False


# =============================================================================
# TEST 2: VALIDAR IMPORTS DE SEGURIDAD
# =============================================================================
def test_imports_security():
    """Verifica que las funciones de seguridad se pueden importar."""
    print("\n🔍 TEST 2: Importando funciones de seguridad...")
    try:
        from app.core.security import (
            hashear_contrasena,
            verificar_contrasena,
            crear_token_acceso,
            verificar_token,
            SECRET_KEY,
            ALGORITHM,
            ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        print("✅ Funciones de seguridad importadas exitosamente")
        print(f"   - hashear_contrasena: {callable(hashear_contrasena)}")
        print(f"   - verificar_contrasena: {callable(verificar_contrasena)}")
        print(f"   - crear_token_acceso: {callable(crear_token_acceso)}")
        print(f"   - verificar_token: {callable(verificar_token)}")
        print(f"   - SECRET_KEY configurado: {bool(SECRET_KEY)}")
        print(f"   - ALGORITHM: {ALGORITHM}")
        print(f"   - ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
        return True
    except Exception as e:
        print(f"❌ Error importando seguridad: {e}")
        return False


# =============================================================================
# TEST 3: VALIDAR IMPORTS DE ANALYTICS
# =============================================================================
def test_imports_analytics():
    """Verifica que las clases de análisis se pueden importar."""
    print("\n🔍 TEST 3: Importando servicios de análisis...")
    try:
        from app.services.analytics import MaintenanceAnalytics, ResumenAnalytica
        print("✅ Servicios de análisis importados exitosamente")
        print(f"   - MaintenanceAnalytics: {MaintenanceAnalytics}")
        print(f"   - ResumenAnalytica: {ResumenAnalytica}")
        return True
    except Exception as e:
        print(f"❌ Error importando analytics: {e}")
        return False


# =============================================================================
# TEST 4: PRUEBA FUNCIONAL - HASHING DE CONTRASEÑAS
# =============================================================================
def test_hashing_contrasenas():
    """Prueba que el hashing de contraseñas funciona correctamente."""
    print("\n🔍 TEST 4: Probando hashing de contraseñas...")
    try:
        from app.core.security import hashear_contrasena, verificar_contrasena

        password = "MiContraseña123!@#"
        hashed = hashear_contrasena(password)

        print(f"   - Contraseña original: {password}")
        print(f"   - Hash generado: {hashed[:20]}...")

        # Verificar contraseña correcta
        es_correcta = verificar_contrasena(password, hashed)
        assert es_correcta, "La verificación debería ser True para contraseña correcta"
        print(f"   ✅ Verificación de contraseña correcta: {es_correcta}")

        # Verificar contraseña incorrecta
        es_incorrecta = verificar_contrasena("OtraContraseña", hashed)
        assert not es_incorrecta, "La verificación debería ser False para contraseña incorrecta"
        print(f"   ✅ Rechazo de contraseña incorrecta: {not es_incorrecta}")

        return True
    except Exception as e:
        print(f"❌ Error en prueba de hashing: {e}")
        return False


# =============================================================================
# TEST 5: PRUEBA FUNCIONAL - TOKENS JWT
# =============================================================================
def test_jwt_tokens():
    """Prueba que los tokens JWT se crean y verifican correctamente."""
    print("\n🔍 TEST 5: Probando tokens JWT...")
    try:
        from app.core.security import crear_token_acceso, verificar_token

        # Crear token
        datos_token = {"sub": "usuario123", "email": "user@example.com", "rol": "Administrador"}
        token = crear_token_acceso(datos_token)

        print(f"   - Token creado: {token[:30]}...")
        print(f"   - Datos del token: {datos_token}")

        # Verificar token
        datos_verificados = verificar_token(token)
        assert datos_verificados is not None, "El token debería ser válido"
        print(f"   ✅ Token verificado exitosamente")
        print(f"   - Usuario (sub): {datos_verificados.get('sub')}")
        print(f"   - Email: {datos_verificados.get('email')}")
        print(f"   - Rol: {datos_verificados.get('rol')}")

        # Verificar token inválido
        token_invalido = crear_token_acceso(
            {"sub": "user2"},
            expira_en=timedelta(seconds=-1)  # Token expirado
        )
        datos_invalidos = verificar_token(token_invalido)
        print(f"   ✅ Token expirado rechazado: {datos_invalidos is None}")

        return True
    except Exception as e:
        print(f"❌ Error en prueba de JWT: {e}")
        return False


# =============================================================================
# TEST 6: PRUEBA FUNCIONAL - ANALYTICS
# =============================================================================
def test_analytics():
    """Prueba que los análisis de mantenimiento funcionan correctamente."""
    print("\n🔍 TEST 6: Probando análisis de mantenimiento...")
    try:
        from app.services.analytics import MaintenanceAnalytics

        # Crear datos de prueba
        mantenimientos: List[Dict] = [
            {
                "equipo_id": 1,
                "equipo_serial": "LG-001",
                "tipo_mantenimiento": "Preventivo",
                "estado_equipo": "Operativo"
            },
            {
                "equipo_id": 2,
                "equipo_serial": "SAMSUNG-002",
                "tipo_mantenimiento": "Correctivo",
                "estado_equipo": "Operativo"
            },
            {
                "equipo_id": 3,
                "equipo_serial": "FUJITSU-003",
                "tipo_mantenimiento": "Preventivo",
                "estado_equipo": "En reparacion"
            },
            {
                "equipo_id": 4,
                "equipo_serial": "LG-004",
                "tipo_mantenimiento": "Correctivo",
                "estado_equipo": "Inactivo"
            },
        ]

        # Calcular métricas
        analytics = MaintenanceAnalytics()
        resumen = analytics.calcular_metricas(mantenimientos)

        print(f"   ✅ Análisis completado")
        print(f"   - Fallas por equipo: {resumen.conteo_fallas_por_equipo}")
        print(f"   - Cumplimiento preventivo: {resumen.porcentaje_cumplimiento_preventivo}%")
        print(f"   - Equipos operativos: {resumen.equipos_operativos}/{resumen.total_equipos}")
        print(f"   - Equipos fuera de servicio: {resumen.equipos_fuera_servicio}/{resumen.total_equipos}")

        # Validaciones
        assert resumen.total_equipos == 4, "Debería haber 4 equipos únicos"
        assert resumen.equipos_operativos == 2, "Debería haber 2 equipos operativos"
        assert resumen.porcentaje_cumplimiento_preventivo == 50.0, "50% deberían ser preventivos"

        return True
    except Exception as e:
        print(f"❌ Error en prueba de analytics: {e}")
        return False


# =============================================================================
# TEST 7: VALIDAR ENUMS
# =============================================================================
def test_enums():
    """Prueba que los enums funcionan correctamente."""
    print("\n🔍 TEST 7: Probando enums...")
    try:
        from app.models import EstadoEquipo, TipoRol

        # Validar EstadoEquipo
        print(f"   Estados de equipo disponibles:")
        for estado in EstadoEquipo:
            print(f"      - {estado.name}: {estado.value}")

        assert EstadoEquipo.OPERATIVO.value == "Operativo"
        assert EstadoEquipo.EN_REPARACION.value == "En reparacion"

        # Validar TipoRol
        print(f"   Roles disponibles:")
        for rol in TipoRol:
            print(f"      - {rol.name}: {rol.value}")

        assert TipoRol.ADMINISTRADOR.value == "Administrador"
        assert TipoRol.TECNICO.value == "Técnico"

        print(f"   ✅ Enums validados correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en prueba de enums: {e}")
        return False


# =============================================================================
# SUITE DE PRUEBAS
# =============================================================================
def ejecutar_todas_las_pruebas():
    """Ejecuta todas las pruebas y proporciona un resumen."""
    print("\n" + "="*70)
    print("🧪 SUITE DE PRUEBAS - SISTEMA DE GESTIÓN DE AIRES")
    print("="*70)

    resultados = {
        "Imports de Modelos": test_imports_modelos(),
        "Imports de Seguridad": test_imports_security(),
        "Imports de Analytics": test_imports_analytics(),
        "Hashing de Contraseñas": test_hashing_contrasenas(),
        "Tokens JWT": test_jwt_tokens(),
        "Analytics": test_analytics(),
        "Enums": test_enums(),
    }

    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)

    total_pruebas = len(resultados)
    pruebas_exitosas = sum(1 for resultado in resultados.values() if resultado)
    pruebas_fallidas = total_pruebas - pruebas_exitosas

    for nombre, resultado in resultados.items():
        estado = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{estado:12} | {nombre}")

    print("\n" + "-"*70)
    print(f"Total: {total_pruebas} | Exitosas: {pruebas_exitosas} | Fallidas: {pruebas_fallidas}")
    print("-"*70)

    if pruebas_fallidas == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("✨ El sistema está listo para producción")
    else:
        print(f"\n⚠️  {pruebas_fallidas} prueba(s) fallaron. Revisa los errores arriba.")

    print("="*70 + "\n")

    return pruebas_fallidas == 0


if __name__ == "__main__":
    exito = ejecutar_todas_las_pruebas()
    sys.exit(0 if exito else 1)

