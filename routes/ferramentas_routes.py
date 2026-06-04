from app import app

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify
)

from datetime import datetime

from database.db import conectar

from utils.auth import (
    login_obrigatorio,
    admin_obrigatorio
)

from utils.logs import registrar_log

# =========================
# REGISTRAR FERRAMENTA
# =========================

@app.route('/registrar', methods=['GET', 'POST'])
@login_obrigatorio
def registrar():

    if request.method == 'POST':

        matricula = request.form['matricula'].strip()
        ferramenta = request.form['ferramenta'].strip()
        nome = request.form['nome'].strip()

        if not matricula or not ferramenta:

            flash(
                'Preencha todos os campos.',
                'alerta'
            )

            return redirect(url_for('registrar'))

        with conectar() as con:

            usuario = con.execute('''
            SELECT *
            FROM usuarios
            WHERE matricula=?
            ''', (matricula,)).fetchone()

            if not usuario:

                if not nome:

                    flash(
                        'Colaborador não encontrado.',
                        'erro'
                    )

                    return redirect(url_for('registrar'))

                con.execute('''
                INSERT INTO usuarios
                (matricula, nome)
                VALUES (?, ?)
                ''', (
                    matricula,
                    nome
                ))

            else:

                nome = usuario['nome']

            ferramenta_existente = con.execute('''
            SELECT *
            FROM ferramentas
            WHERE LOWER(ferramenta)=LOWER(?)
            ''', (ferramenta,)).fetchone()

            if ferramenta_existente:

                flash(
                    'Ferramenta já emprestada.',
                    'erro'
                )

                return redirect(url_for('registrar'))

            data_registro = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )

            con.execute('''
            INSERT INTO ferramentas
            (
                matricula,
                nome,
                ferramenta,
                data_registro,
                retirado_por_usuario,
                retirado_por_nome
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                matricula,
                nome,
                ferramenta,
                data_registro,
                session['usuario'],
                session['usuario_nome']
            ))

            registrar_log(
                f'RETIRADA: {nome} retirou "{ferramenta}" '
                f'| registrado por {session["usuario_nome"]}'
            )

        flash(
            'Ferramenta registrada com sucesso.',
            'sucesso'
        )

        return redirect(url_for('index'))

    return render_template('registrar.html')


# =========================
# EDITAR
# =========================

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
@admin_obrigatorio
def editar(id):

    with conectar() as con:

        ferramenta = con.execute('''
        SELECT *
        FROM ferramentas
        WHERE id=?
        ''', (id,)).fetchone()

        if not ferramenta:

            return redirect(url_for('index'))

        if request.method == 'POST':

            nome = request.form['nome'].strip()
            matricula = request.form['matricula'].strip()
            ferramenta_nome = request.form['ferramenta'].strip()

            con.execute('''
            UPDATE ferramentas
            SET nome=?,
                matricula=?,
                ferramenta=?
            WHERE id=?
            ''', (
                nome,
                matricula,
                ferramenta_nome,
                id
            ))

            registrar_log(
                f'EDIÇÃO: ferramenta ID {id} alterada por '
                f'{session["usuario_nome"]}'
            )

            return redirect(url_for('index'))

    return render_template(
        'editar.html',
        ferramenta=ferramenta
    )


# =========================
# BAIXAR FERRAMENTA
# =========================

@app.route('/baixar/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def baixar(id):

    with conectar() as con:

        ferramenta = con.execute('''
        SELECT *
        FROM ferramentas
        WHERE id=?
        ''', (id,)).fetchone()

        if not ferramenta:

            return redirect(url_for('index'))

        if request.method == 'POST':

            matricula_devolucao = request.form['matricula'].strip()

            usuario_devolucao = con.execute('''
            SELECT *
            FROM usuarios
            WHERE matricula=?
            ''', (matricula_devolucao,)).fetchone()

            if not usuario_devolucao:

                flash(
                    'Colaborador não encontrado.',
                    'erro'
                )

                return redirect(
                    url_for('baixar', id=id)
                )

            data_baixa = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            con.execute('''
            INSERT INTO baixadas
            (
                matricula,
                nome,
                ferramenta,

                devolvido_por_matricula,
                devolvido_por_nome,

                data_retirada,
                data_baixa,

                registrado_por_usuario,
                registrado_por_nome,

                devolucao_registrada_por_usuario,
                devolucao_registrada_por_nome
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ferramenta['matricula'],
                ferramenta['nome'],
                ferramenta['ferramenta'],

                usuario_devolucao['matricula'],
                usuario_devolucao['nome'],

                ferramenta['data_registro'],
                data_baixa,

                ferramenta['retirado_por_usuario'],
                ferramenta['retirado_por_nome'],

                session['usuario'],
                session['usuario_nome']
            ))

            con.execute('''
            DELETE FROM ferramentas
            WHERE id=?
            ''', (id,))

            registrar_log(
                f'DEVOLUÇÃO: {ferramenta["nome"]} devolveu '
                f'"{ferramenta["ferramenta"]}" '
                f'| recebido por {session["usuario_nome"]}'
            )

            return redirect(url_for('index'))

    return render_template(
        'baixar.html',
        ferramenta=ferramenta
    )

# =========================
# BUSCAR COLABORADOR
# =========================

@app.route('/buscar_colaborador/<matricula>')
@login_obrigatorio
def buscar_colaborador(matricula):

    with conectar() as con:

        usuario = con.execute('''
        SELECT *
        FROM usuarios
        WHERE matricula=?
        ''', (matricula.strip(),)).fetchone()

    if usuario:

        return jsonify({
            'encontrado': True,
            'nome': usuario['nome']
        })

    return jsonify({
        'encontrado': False
    })