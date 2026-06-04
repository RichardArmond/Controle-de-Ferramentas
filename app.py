from flask import Flask
from dotenv import load_dotenv

import os

load_dotenv()

app = Flask(__name__)

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.secret_key = os.getenv('SECRET_KEY')

# =========================
# IMPORTAR ROTAS
# =========================

from routes.index_routes import *
from routes.auth_routes import *
from routes.backup_routes import *
from routes.ferramentas_routes import *
from routes.colaboradores_routes import *
from routes.usuarios_routes import *
from routes.historico_routes import *
#from routes.fixas_routes import *#

# =========================
# BANCO
# =========================

from database.db import criar_tabelas

criar_tabelas()

# =========================
# EXECUTAR
# =========================

if __name__ == '__main__':

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5001
    )