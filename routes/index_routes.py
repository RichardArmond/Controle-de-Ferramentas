from app import app

from flask import (
    render_template,
    request
)

from datetime import datetime

from database.db import conectar

from utils.auth import login_obrigatorio

@app.route('/')
@login_obrigatorio
def index():

    busca = request.args.get('busca', '').strip()

    with conectar() as con:

        if busca:

            busca_like = f'%{busca}%'

            ferramentas = con.execute('''
            SELECT *
            FROM ferramentas
            WHERE LOWER(nome) LIKE LOWER(?)
               OR LOWER(ferramenta) LIKE LOWER(?)
               OR LOWER(matricula) LIKE LOWER(?)
            ORDER BY data_registro DESC
            ''', (
                busca_like,
                busca_like,
                busca_like
            )).fetchall()

        else:

            ferramentas = con.execute('''
            SELECT *
            FROM ferramentas
            ORDER BY data_registro DESC
            ''').fetchall()

        lista_ferramentas = []

        atrasadas = []

        for f in ferramentas:

            item = dict(f)

            try:

                retirada = datetime.strptime(
                    f['data_registro'],
                    '%Y-%m-%d %H:%M:%S'
                )

                agora = datetime.now()

                diferenca = agora - retirada

                horas = int(diferenca.total_seconds() / 3600)

                item['horas_fora'] = horas

                if horas >= 24:

                    item['status'] = 'danger'

                    atrasadas.append(item)

                elif horas >= 12:

                    item['status'] = 'warning'

                else:

                    item['status'] = 'success'

            except Exception:

                item['horas_fora'] = 0
                item['status'] = 'success'

            lista_ferramentas.append(item)

        total_ferramentas = con.execute('''
        SELECT COUNT(*)
        FROM ferramentas
        ''').fetchone()[0]

        total_colaboradores = con.execute('''
        SELECT COUNT(*)
        FROM usuarios
        ''').fetchone()[0]

        baixadas_hoje = con.execute('''
        SELECT COUNT(*)
        FROM baixadas
        WHERE DATE(data_baixa)=DATE('now', 'localtime')
        ''').fetchone()[0]

        ultima_retirada = con.execute('''
        SELECT nome, ferramenta
        FROM ferramentas
        ORDER BY id DESC
        LIMIT 1
        ''').fetchone()

    return render_template(
        'index.html',
        ferramentas=lista_ferramentas,
        atrasadas=atrasadas,
        busca=busca,
        total_ferramentas=total_ferramentas,
        total_colaboradores=total_colaboradores,
        baixadas_hoje=baixadas_hoje,
        ultima_retirada=ultima_retirada
    )