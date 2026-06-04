from app import app

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session
)

from database.db import conectar

from utils.auth import (
    login_obrigatorio,
    admin_obrigatorio
)

from utils.logs import registrar_log

from utils.mensagens import mensagem

# =========================
# COLABORADORES
# =========================

@app.route('/colaboradores', methods=['GET', 'POST'])
@login_obrigatorio
@admin_obrigatorio
def colaboradores():

    with conectar() as con:

        if request.method == 'POST':

            matricula = request.form['matricula'].strip()
            nome = request.form['nome'].strip()

            if matricula and nome:

                usuario = con.execute('''
                SELECT *
                FROM usuarios
                WHERE matricula=?
                ''', (matricula,)).fetchone()

                if not usuario:

                    con.execute('''
                    INSERT INTO usuarios
                    (matricula, nome)
                    VALUES (?, ?)
                    ''', (
                        matricula,
                        nome
                    ))

        colaboradores = con.execute('''
        SELECT *
        FROM usuarios
        ORDER BY nome ASC
        ''').fetchall()

    return render_template(
        'colaboradores.html',
        colaboradores=colaboradores
    )


# =========================
# EXCLUIR COLABORADOR
# =========================

@app.route('/excluir_colaborador/<int:id>')
@login_obrigatorio
@admin_obrigatorio
def excluir_colaborador(id):

    with conectar() as con:

        colaborador = con.execute('''
        SELECT *
        FROM usuarios
        WHERE id=?
        ''', (id,)).fetchone()

        if not colaborador:

            return redirect(url_for('colaboradores'))

        ferramenta_pendente = con.execute('''
        SELECT *
        FROM ferramentas
        WHERE matricula=?
        ''', (colaborador['matricula'],)).fetchone()

        if ferramenta_pendente:

            return mensagem(
                'Exclusão não permitida',
                'O colaborador possui ferramenta pendente.',
                'alerta',
                '/colaboradores'
            )

        registrar_log(
            f'COLABORADOR EXCLUÍDO: '
            f'{colaborador["nome"]} '
            f'({colaborador["matricula"]}) '
            f'por {session["usuario_nome"]}'
        )

        con.execute('''
        DELETE FROM usuarios
        WHERE id=?
        ''', (id,))

    return redirect(url_for('colaboradores'))