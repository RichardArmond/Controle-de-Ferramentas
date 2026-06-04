import os
import shutil

from datetime import datetime

from database.db import BANCO

PASTA_BACKUP = 'backup'

if not os.path.exists(PASTA_BACKUP):

    os.makedirs(PASTA_BACKUP)

def gerar_backup():

    if not os.path.exists(BANCO):

        return

    data_backup = datetime.now().strftime(
        '%Y-%m-%d_%H-%M-%S'
    )

    nome_backup = f'backup_{data_backup}.db'

    destino = os.path.join(
        PASTA_BACKUP,
        nome_backup
    )

    shutil.copy2(BANCO, destino)

    print(f'Backup criado: {destino}')