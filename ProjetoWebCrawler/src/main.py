from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "db", "retro_games.db")

app = FastAPI(
    title="Retro Playlist Engine API",
    description="Motor de recomendação de jogos retrô com links para Gameplay (EXA618)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Jogo(BaseModel):
    url: str
    titulo: str
    ano: int
    genero: Optional[str] = None
    plataforma: Optional[str] = None
    nota: float
    votos: int
    imagem_url: Optional[str] = None
    link_download: Optional[str] = None
    link_youtube: str 
    data_extracao: str

def obter_conexao_db():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Banco de dados não encontrado.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def formatar_jogo_com_youtube(row):
    jogo_dict = dict(row)
    titulo_formatado = urllib.parse.quote_plus(f"Gameplay Retro {jogo_dict['titulo']}")
    jogo_dict['link_youtube'] = f"https://www.youtube.com/results?search_query={titulo_formatado}"
    return jogo_dict

@app.get("/", tags=["Status"])
def verificar_status():

    return {"status": "Online", "mensagem": "API a funcionar perfeitamente!"}

@app.get("/categorias/generos", response_model=List[str], tags=["Metadados"])
def listar_generos_unicos():
    conn = obter_conexao_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT genero FROM jogos WHERE genero IS NOT NULL AND genero != 'Não encontrado' ORDER BY genero")
    generos = [row['genero'] for row in cursor.fetchall()]
    conn.close()
    return generos

@app.get("/categorias/plataformas", response_model=List[str], tags=["Metadados"])
def listar_plataformas_unicas():
    conn = obter_conexao_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT plataforma FROM jogos WHERE plataforma IS NOT NULL AND plataforma != 'Não encontrado' ORDER BY plataforma")
    plataformas = [row['plataforma'] for row in cursor.fetchall()]
    conn.close()
    return plataformas

@app.get("/jogos/playlist", response_model=List[Jogo], tags=["Playlist Engine"])
def gerar_playlist(
    genero: Optional[List[str]] = Query(None, description="Filtro de Género"),
    plataforma: Optional[List[str]] = Query(None, description="Filtro de Plataforma"),
    ano_inicio: int = Query(1993, description="Ano inicial"),
    ano_fim: int = Query(2000, description="Ano final"),
    nota_minima: float = Query(4.0, description="Nota mínima (0.0 a 5.0)"),
    votos_minimos: int = Query(0, description="Quantidade mínima de votos"), 
    tamanho_playlist: int = Query(12, description="Quantidade de jogos", le=50)
):
    conn = obter_conexao_db()
    cursor = conn.cursor()
    
   
    query = "SELECT * FROM jogos WHERE ano >= ? AND ano <= ? AND CAST(nota AS FLOAT) >= ? AND votos >= ?"
    parametros = [ano_inicio, ano_fim, nota_minima, votos_minimos]
    
    if genero:
        clausulas = " OR ".join(["genero LIKE ?"] * len(genero))
        query += f" AND ({clausulas})"
        for g in genero:
            parametros.append(f"%{g}%")
            
    if plataforma:
        clausulas = " OR ".join(["plataforma LIKE ?"] * len(plataforma))
        query += f" AND ({clausulas})"
        for p in plataforma:
            parametros.append(f"%{p}%")
        
    query += " ORDER BY nota DESC, votos DESC LIMIT ?"
    parametros.append(tamanho_playlist)
    
    cursor.execute(query, parametros)
    jogos = [formatar_jogo_com_youtube(row) for row in cursor.fetchall()]
    conn.close()
    
    if not jogos:
        raise HTTPException(status_code=404, detail="Nenhum jogo atende a estes critérios.")
        
    return jogos