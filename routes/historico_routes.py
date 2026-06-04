from app import app

from flask import render_template

from datetime import datetime

from database.db import conectar

from utils.auth import login_obrigatorio

# =========================
# HISTÓRICO
# =========================

@app.route('/baixadas')
@login_obrigatorio
def baixadas():

    with conectar() as con:

        baixadas = con.execute('''
        SELECT *
        FROM baixadas
        ORDER BY data_baixa DESC
        ''').fetchall()

        lista = []

        for b in baixadas:

            item = dict(b)

            try:

                retirada = datetime.strptime(
                    b['data_retirada'],
                    '%Y-%m-%d %H:%M:%S'
                )

                devolucao = datetime.strptime(
                    b['data_baixa'],
                    '%Y-%m-%d %H:%M:%S'
                )

                diferenca = devolucao - retirada

                dias = diferenca.days
                horas = diferenca.seconds // 3600

                if dias > 0:

                    tempo = f'{dias}d {horas}h'

                else:

                    tempo = f'{horas}h'

                item['tempo_total'] = tempo

            except Exception:

                item['tempo_total'] = '-'

            lista.append(item)

    return render_template(
        'baixadas.html',
        baixadas=lista
    )
