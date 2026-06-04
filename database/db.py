import sqlite3
import os

from werkzeug.security import generate_password_hash

from dotenv import load_dotenv

from utils.logs import registrar_log

load_dotenv()

ADMIN_USUARIO = os.getenv('ADMIN_USUARIO')
ADMIN_SENHA = os.getenv('ADMIN_SENHA')
ADMIN_NOME = os.getenv('ADMIN_NOME')

BANCO = 'ferramentas_novo.db'

def conectar():

    con = sqlite3.connect(
        BANCO,
        check_same_thread=False
    )

    con.row_factory = sqlite3.Row

    return con

# =========================
# CRIAR TABELAS
# =========================

def criar_tabelas():

    with conectar() as con:

        # =========================
        # USUÁRIOS DO SISTEMA
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS sistema_usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
        ''')

        # =========================
        # COLABORADORES
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL
        )
        ''')

        # =========================
        # FERRAMENTAS
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS ferramentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            matricula TEXT NOT NULL,
            nome TEXT NOT NULL,

            ferramenta TEXT NOT NULL,

            data_registro TEXT NOT NULL,

            retirado_por_usuario TEXT,
            retirado_por_nome TEXT
        )
        ''')

        # =========================
        # HISTÓRICO
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS baixadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            matricula TEXT NOT NULL,
            nome TEXT NOT NULL,

            ferramenta TEXT NOT NULL,

            devolvido_por_matricula TEXT NOT NULL,
            devolvido_por_nome TEXT NOT NULL,

            data_retirada TEXT,
            data_baixa TEXT NOT NULL,

            registrado_por_usuario TEXT,
            registrado_por_nome TEXT,

            devolucao_registrada_por_usuario TEXT,
            devolucao_registrada_por_nome TEXT
        )
        ''')

        admin_existe = con.execute('''
        SELECT *
        FROM sistema_usuarios
        WHERE tipo='admin'
        ''').fetchone()

        if not admin_existe:

            senha_hash = generate_password_hash(
                ADMIN_SENHA
            )

            con.execute('''
            INSERT INTO sistema_usuarios
            (
                usuario,
                senha,
                nome,
                tipo
            )
            VALUES (?, ?, ?, ?)
            ''', (
                ADMIN_USUARIO,
                senha_hash,
                ADMIN_NOME,
                'admin'
            ))

            registrar_log(
                'ADMIN PRINCIPAL CRIADO'
            )

        # =========================
        # OPERADOR PADRÃO
        # =========================

        operador = con.execute('''
        SELECT *
        FROM sistema_usuarios
        WHERE usuario=?
        ''', ('operador',)).fetchone()

        if not operador:

            senha_operador = generate_password_hash('123')

            con.execute('''
            INSERT INTO sistema_usuarios
            (
                usuario,
                senha,
                nome,
                tipo
            )
            VALUES (?, ?, ?, ?)
            ''', (
                'operador',
                senha_operador,
                'Operador',
                'operador'
            ))
            con.commit()
            
