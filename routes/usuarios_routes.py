from app import app

import os

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from dotenv import load_dotenv

from werkzeug.security import generate_password_hash

from database.db import conectar

from utils.auth import (
    login_obrigatorio,
    admin_obrigatorio
)

from utils.logs import registrar_log

from utils.mensagens import mensagem

load_dotenv()

ADMIN_USUARIO = os.getenv('ADMIN_USUARIO')

# =========================
# USUÁRIOS DO SISTEMA
# =========================

@app.route('/usuarios_sistema', methods=['GET', 'POST'])
@login_obrigatorio
@admin_obrigatorio
def usuarios_sistema():

    with conectar() as con:

        if request.method == 'POST':

            usuario = request.form.get('usuario', '').strip()
            senha = request.form.get('senha', '').strip()
            nome = request.form['nome'].strip()
            tipo = request.form['tipo'].strip()

            existente = con.execute('''
            SELECT *
            FROM sistema_usuarios
            WHERE usuario=?
            ''', (usuario,)).fetchone()

            if existente:

                flash(
                    'Usuário já existe.',
                    'erro'
                )

                return redirect(
                    url_for('usuarios_sistema')
                )

            senha_hash = generate_password_hash(senha)

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
                usuario,
                senha_hash,
                nome,
                tipo
            ))

            registrar_log(
                f'USUÁRIO CRIADO: '
                f'{nome} ({usuario}) '
                f'| tipo: {tipo} '
                f'| criado por {session["usuario_nome"]}'
            )

        usuarios = con.execute('''
        SELECT *
        FROM sistema_usuarios
        ORDER BY nome ASC
        ''').fetchall()

    return render_template(
        'usuarios_sistema.html',
        usuarios=usuarios
    )

# =========================
# EXCLUIR USUÁRIO SISTEMA
# =========================

@app.route('/excluir_usuario_sistema/<int:id>')
@login_obrigatorio
@admin_obrigatorio
def excluir_usuario_sistema(id):

    with conectar() as con:

        usuario = con.execute('''
        SELECT *
        FROM sistema_usuarios
        WHERE id=?
        ''', (id,)).fetchone()

        if not usuario:

            return redirect(url_for('usuarios_sistema'))

        # =========================
        # NÃO PERMITE EXCLUIR
        # O ADMIN PRINCIPAL
        # =========================

        if usuario['usuario'] == ADMIN_USUARIO:

            registrar_log(
                f'TENTATIVA DE EXCLUIR ADMIN PRINCIPAL '
                f'por {session["usuario_nome"]}'
            )

            return mensagem(
                'Ação não permitida',
                'Não é permitido excluir o administrador principal.',
                'erro',
                '/usuarios_sistema'
            )

        # =========================
        # NÃO PERMITE EXCLUIR
        # O PRÓPRIO USUÁRIO
        # =========================

        if usuario['id'] == session['usuario_id']:

            flash(
                'Você não pode excluir seu próprio usuário.',
                'alerta'
            )

            return redirect(
                url_for('usuarios_sistema')
            )

        registrar_log(
            f'USUÁRIO EXCLUÍDO: '
            f'{usuario["nome"]} ({usuario["usuario"]}) '
            f'por {session["usuario_nome"]}'
        )

        con.execute('''
        DELETE FROM sistema_usuarios
        WHERE id=?
        ''', (id,))

    return redirect(url_for('usuarios_sistema'))
