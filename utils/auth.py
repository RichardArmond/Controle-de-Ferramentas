from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash
)

from database.db import conectar

def login_obrigatorio(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        usuario_id = session.get('usuario_id')

        if not usuario_id:

            return redirect(url_for('login'))

        # =========================
        # VERIFICA SE O USUÁRIO
        # AINDA EXISTE NO BANCO
        # =========================

        with conectar() as con:

            usuario = con.execute('''
            SELECT *
            FROM sistema_usuarios
            WHERE id=?
            ''', (usuario_id,)).fetchone()

        # =========================
        # USUÁRIO FOI EXCLUÍDO
        # =========================

        if not usuario:

            session.clear()

            flash(
                'Sua sessão expirou.',
                'alerta'
            )

            return redirect(url_for('login'))

        # =========================
        # ATUALIZA DADOS DA SESSÃO
        # CASO O TIPO MUDE
        # =========================

        session['usuario_nome'] = usuario['nome']
        session['usuario'] = usuario['usuario']
        session['tipo'] = usuario['tipo']

        return f(*args, **kwargs)

    return decorated_function


def admin_obrigatorio(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get('tipo') != 'admin':

            flash(
                'Acesso permitido apenas para administradores.',
                'erro'
            )

            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function