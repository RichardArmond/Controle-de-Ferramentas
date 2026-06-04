from datetime import datetime
import os

LOGS = 'logs'

if not os.path.exists(LOGS):

    os.makedirs(LOGS)

def registrar_log(mensagem):

    data_log = datetime.now().strftime(
        '%Y-%m-%d'
    )

    arquivo_log = os.path.join(
        LOGS,
        f'log_{data_log}.txt'
    )

    horario = datetime.now().strftime(
        '%d/%m/%Y %H:%M:%S'
    )

    with open(
        arquivo_log,
        'a',
        encoding='utf-8'
    ) as log:

        log.write(
            f'[{horario}] {mensagem}\n'
        )