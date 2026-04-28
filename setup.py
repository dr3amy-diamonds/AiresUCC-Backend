"""
Setup para instalación del proyecto aires-ucc como librería.
Instalar con: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="aires-ucc",
    version="0.1.0",
    description="Sistema de gestión de aires acondicionados UCC",
    packages=find_packages(include=["backend", "backend.*"]),
    python_requires=">=3.9",
    install_requires=[
        # FastAPI y Servidor Web
        "fastapi==0.136.0",
        "uvicorn==0.45.0",
        "python-multipart==0.0.26",
        
        # Base de Datos
        "sqlalchemy==2.0.49",
        "psycopg2-binary==2.9.12",
        "alembic==1.18.4",
        
        # Validación de Datos
        "pydantic==2.13.3",
        "pydantic-settings==2.14.0",
        "email-validator==2.1.0",
        
        # Análisis de Datos
        "pandas==3.0.2",
        "numpy==2.4.4",
        "plotly==6.7.0",
        
        # Seguridad
        "passlib==1.7.4",
        "bcrypt==5.0.0",
        "python-jose==3.5.0",
        "cryptography==46.0.7",
        
        # Configuración
        "python-dotenv==1.2.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0",
            "flake8>=6.0",
            "isort>=5.12",
            "mypy>=1.0",
            "ipython>=8.0",
        ]
    },
    author="Grupo Desarrollo",
    author_email="desarrollo@ucc.edu.co",
    license="MIT",
)

