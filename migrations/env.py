import asyncio
import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Adiciona a raiz do projeto para o Python encontrar a pasta 'app'
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Importa a URL do banco e a Base
from app.core.database import Base, DATABASE_URL

# 3. IMPORTAÇÃO OBRIGATÓRIA DOS MODELOS (Se não importar aqui, o Alembic não cria a tabela)
from app.modulos.empresas.models import Empresa, CredencialAPI

from app.modulos.apis.sungrow.models import SungrowConfig
from app.modulos.apis.solis.models import SolisConfig

from app.modulos.apis.models import CacheAPI

# Configurações nativas do Alembic
config = context.config

# 4. Força o Alembic a usar a URL do nosso código (ignora o alembic.ini)
config.set_main_option("sqlalchemy.url", str(DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 5. Aponta os metadados para o Alembic ler
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações no modo offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria a engine assíncrona e roda as migrações."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Executa migrações no modo online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()