from app import app

from flask import (
    redirect,
    url_for,
    flash,
    session,
    render_template
)

import os
import shutil

from datetime import datetime

from utils.auth import (
    login_obrigatorio,
    admin_obrigatorio
)

from utils.logs import registrar_log

from utils.backup import (
    gerar_backup,
    PASTA_BACKUP
)

from database.db import BANCO

# =========================
# GERAR BACKUP MANUAL
# =========================

@app.route('/gerar_backup')
@login_obrigatorio
@admin_obrigatorio
def gerar_backup_manual():

    gerar_backup()

    registrar_log(
        f'BACKUP MANUAL: {session["usuario_nome"]}'
    )

    flash(
        'Backup gerado com sucesso.',
        'sucesso'
    )

    return redirect(url_for('backups'))

# =========================
# RESTAURAR BACKUP
# =========================

@app.route('/restaurar_backup/<nome_arquivo>')
@login_obrigatorio
@admin_obrigatorio
def restaurar_backup(nome_arquivo):

    caminho_backup = os.path.join(
        PASTA_BACKUP,
        nome_arquivo
    )

    if not os.path.exists(caminho_backup):

        flash(
            'Backup não encontrado.',
            'erro'
        )

        return redirect(url_for('backups'))

    shutil.copy2(caminho_backup, BANCO)

    registrar_log(
        f'BACKUP RESTAURADO: {nome_arquivo} por {session["usuario_nome"]}'
    )

    flash(
        'Backup restaurado com sucesso.',
        'sucesso'
    )

    return redirect(url_for('backups'))

# =========================
# LISTA BACKUPS
# =========================

@app.route('/backups')
@login_obrigatorio
@admin_obrigatorio
def backups():

    arquivos = []

    for arquivo in os.listdir(PASTA_BACKUP):

        if arquivo.endswith('.db'):

            caminho = os.path.join(
                PASTA_BACKUP,
                arquivo
            )

            data_modificacao = datetime.fromtimestamp(
                os.path.getmtime(caminho)
            )

            arquivos.append({
                'nome': arquivo,
                'data': data_modificacao.strftime(
                    '%d/%m/%Y %H:%M:%S'
                )
            })

    arquivos.sort(
        key=lambda x: x['data'],
        reverse=True
    )

    return render_template(
        'backups.html',
        backups=arquivos
    )