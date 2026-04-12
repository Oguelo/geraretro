import sqlite3
import os

PASTA_DATA = os.path.join(os.path.dirname(__file__), '..', 'db')
NOME_BANCO = os.path.join(PASTA_DATA, 'retro_games.db')
def obter_conexao():
    return sqlite3.connect(NOME_BANCO)

def inicializar_banco():
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogos (
            url TEXT PRIMARY KEY,
            titulo TEXT,
            ano INTEGER,
            genero TEXT,
            plataforma TEXT,
            nota REAL,
            votos INTEGER,      
            imagem_url TEXT,
            link_download TEXT,
            data_extracao TEXT
        )
    ''')
    conn.commit()
    conn.close()

inicializar_banco()