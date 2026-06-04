from flask import render_template

def mensagem(
    titulo,
    texto,
    tipo='alerta',
    voltar='/'
):

    return render_template(
        'mensagem.html',
        titulo=titulo,
        mensagem=texto,
        tipo=tipo,
        voltar=voltar
    )