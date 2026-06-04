from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session
)

import sqlite3

from datetime import datetime

from functools import wraps

import os
import shutil


app = Flask(__name__)

app.secret_key = 'ibar_secret_key'


# =========================
# BANCO
# =========================

BANCO = 'ferramentas_novo.db'

PASTA_BACKUP = 'backup'

if not os.path.exists(PASTA_BACKUP):

    os.makedirs(PASTA_BACKUP)


# =========================
# CONEXÃO
# =========================

def conectar():

    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row

    return con


# =========================
# LOGIN OBRIGATÓRIO
# =========================

def login_obrigatorio(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'usuario_id' not in session:

            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


# =========================
# SOMENTE ADMIN
# =========================

def admin_obrigatorio(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get('tipo') != 'admin':

            return '''
            <h2 style="font-family:Arial;padding:20px;">
                Acesso permitido apenas para ADMIN.
            </h2>

            <a href="/">Voltar</a>
            '''

        return f(*args, **kwargs)

    return decorated_function

# =========================
# BACKUP AUTOMÁTICO
# =========================

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

# =========================
# CRIAR TABELAS
# =========================

def criar_tabelas():

    with conectar() as con:

        # =========================
        # USUÁRIOS DO SISTEMA
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS sistema_usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
        ''')

        # =========================
        # COLABORADORES
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL
        )
        ''')

        # =========================
        # FERRAMENTAS
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS ferramentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            matricula TEXT NOT NULL,
            nome TEXT NOT NULL,

            ferramenta TEXT NOT NULL,

            data_registro TEXT NOT NULL,

            retirado_por_usuario TEXT,
            retirado_por_nome TEXT
        )
        ''')

        # =========================
        # HISTÓRICO
        # =========================

        con.execute('''
        CREATE TABLE IF NOT EXISTS baixadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            matricula TEXT NOT NULL,
            nome TEXT NOT NULL,

            ferramenta TEXT NOT NULL,

            devolvido_por_matricula TEXT NOT NULL,
            devolvido_por_nome TEXT NOT NULL,

            data_retirada TEXT,
            data_baixa TEXT NOT NULL,

            registrado_por_usuario TEXT,
            registrado_por_nome TEXT,

            devolucao_registrada_por_usuario TEXT,
            devolucao_registrada_por_nome TEXT
        )
        ''')

        # =========================
        # ADMIN PADRÃO
        # =========================

        admin = con.execute('''
        SELECT *
        FROM sistema_usuarios
        WHERE usuario=?
        ''', ('Richard Armond',)).fetchone()

        if not admin:

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
                'Richard Armond',
                'solda',
                'Richard Armond',
                'admin'
            ))

        # =========================
        # OPERADOR PADRÃO
        # =========================

        operador = con.execute('''
        SELECT *
        FROM sistema_usuarios
        WHERE usuario=?
        ''', ('operador',)).fetchone()

        if not operador:

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
                'operador',
                '123',
                'Operador',
                'operador'
            ))

criar_tabelas()
gerar_backup()

# =========================
# GERAR BACKUP MANUAL
# =========================

@app.route('/gerar_backup')
@login_obrigatorio
@admin_obrigatorio
def gerar_backup_manual():

    gerar_backup()

    return '''
    <h2 style="font-family:Arial;padding:20px;">
        Backup gerado com sucesso.
    </h2>

    <a href="/">Voltar</a>
    '''

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
            AND senha=?
            ''', (
                usuario,
                senha
            )).fetchone()

        if user:

            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            session['usuario'] = user['usuario']
            session['tipo'] = user['tipo']

            return redirect(url_for('index'))

        return '''
        <h2 style="font-family:Arial;padding:20px;">
            Usuário ou senha inválidos.
        </h2>

        <a href="/login">Voltar</a>
        '''

    return render_template('login.html')


# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# =========================
# HOME
# =========================

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

        # =========================
        # ALERTAS DE ATRASO
        # =========================

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

                # STATUS VISUAL

                if horas >= 24:

                    item['status'] = 'danger'

                    atrasadas.append(item)

                elif horas >= 12:

                    item['status'] = 'warning'

                else:

                    item['status'] = 'success'

            except:

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
        WHERE DATE(data_baixa)=DATE('now')
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

            return redirect(url_for('registrar'))

        with conectar() as con:

            usuario = con.execute('''
            SELECT *
            FROM usuarios
            WHERE matricula=?
            ''', (matricula,)).fetchone()

            if not usuario:

                if not nome:

                    return '''
                    <h2 style="font-family:Arial;padding:20px;">
                        Colaborador não encontrado.
                    </h2>

                    <a href="/registrar">Voltar</a>
                    '''

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

                return '''
                <h2 style="font-family:Arial;padding:20px;">
                    Ferramenta já retirada.
                </h2>

                <a href="/">Voltar</a>
                '''

            data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

                return '''
                <h2 style="font-family:Arial;padding:20px;">
                    Colaborador não encontrado.
                </h2>

                <a href="/">Voltar</a>
                '''

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

            return redirect(url_for('index'))

    return render_template(
        'baixar.html',
        ferramenta=ferramenta
    )


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

            return '''
            <h2 style="font-family:Arial;padding:20px;">
                Não é possível excluir.
                Colaborador possui ferramenta pendente.
            </h2>

            <a href="/colaboradores">Voltar</a>
            '''

        con.execute('''
        DELETE FROM usuarios
        WHERE id=?
        ''', (id,))

    return redirect(url_for('colaboradores'))

# =========================
# USUÁRIOS DO SISTEMA
# =========================

@app.route('/usuarios_sistema', methods=['GET', 'POST'])
@login_obrigatorio
@admin_obrigatorio
def usuarios_sistema():

    with conectar() as con:

        if request.method == 'POST':

            usuario = request.form['usuario'].strip()
            senha = request.form['senha'].strip()
            nome = request.form['nome'].strip()
            tipo = request.form['tipo'].strip()

            existente = con.execute('''
            SELECT *
            FROM sistema_usuarios
            WHERE usuario=?
            ''', (usuario,)).fetchone()

            if existente:

                return '''
                <h2 style="font-family:Arial;padding:20px;">
                    Usuário já existe.
                </h2>

                <a href="/usuarios_sistema">Voltar</a>
                '''

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
                senha,
                nome,
                tipo
            ))

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

        # NÃO PERMITE EXCLUIR O ADMIN PRINCIPAL

        if usuario['usuario'] == 'Richard Armond':

            return '''
            <h2 style="font-family:Arial;padding:20px;">
                Não é permitido excluir o administrador principal.
            </h2>

            <a href="/usuarios_sistema">Voltar</a>
            '''

        # NÃO PERMITE EXCLUIR A SI MESMO

        if usuario['id'] == session['usuario_id']:

            return '''
            <h2 style="font-family:Arial;padding:20px;">
                Você não pode excluir seu próprio usuário.
            </h2>

            <a href="/usuarios_sistema">Voltar</a>
            '''

        con.execute('''
        DELETE FROM sistema_usuarios
        WHERE id=?
        ''', (id,))

    return redirect(url_for('usuarios_sistema'))
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

            except:

                item['tempo_total'] = '-'

            lista.append(item)

    return render_template(
        'baixadas.html',
        baixadas=lista
    )


# =========================
# EXECUTAR
# =========================

if __name__ == '__main__':

    app.run(
        debug=True,
        port=5001
    )