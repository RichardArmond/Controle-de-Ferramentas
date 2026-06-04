from app import app

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    check_password_hash
)

from database.db import conectar

from utils.logs import registrar_log

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form['usuario'].strip()
        senha = request.form['senha'].strip()

        with conectar() as con:

            user = con.execute('''
            SELECT *
            FROM sistema_usuarios
            WHERE usuario=?
            ''', (usuario,)).fetchone()

        if user and check_password_hash(
            user['senha'],
            senha
        ):

            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            session['usuario'] = user['usuario']
            session['tipo'] = user['tipo']

            registrar_log(
                f'LOGIN: {user["nome"]} ({user["usuario"]})'
            )

            return redirect(url_for('index'))

        flash(
            'Usuário ou senha incorretos.',
            'erro'
        )

        return redirect(url_for('login'))

    return render_template('login.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    if 'usuario_nome' in session:

        registrar_log(
            f'LOGOUT: {session["usuario_nome"]} ({session["usuario"]})'
        )

    session.clear()

    return redirect(url_for('login'))