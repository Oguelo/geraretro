import concurrent.futures
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from constants import ANOS_PROCESSO, LIMITE_PAGINAS, HEADERS, THREADS_MAX, BASE_URL
from database import obter_conexao, inicializar_banco
from scraper import extrair_dados_jogo

def buscar_links_do_ano(ano):
    links = []
    for p in range(1, LIMITE_PAGINAS + 1):
        url = f"{BASE_URL}/browse/year/{ano}/" if p == 1 else f"{BASE_URL}/browse/year/{ano}/page/{p}/"
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 404: break
            soup = BeautifulSoup(res.text, 'html.parser')
            tags = soup.find_all('a', class_='name')
            if not tags: break
            for t in tags:
                links.append(f"{BASE_URL}{t['href']}")
            time.sleep(1.5)
        except: break
    return links

def rodar_populador():
    inicializar_banco()
    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    
    cursor.execute("SELECT url FROM jogos")
    urls_salvas = {linha[0] for linha in cursor.fetchall()}

    for ano in ANOS_PROCESSO:
        # Busca os links da listagem do ano   print(f"\n--- 📅 Processando {ano} ---")
        
     
        links_do_ano = buscar_links_do_ano(ano)
        links_novos = [l for l in links_do_ano if l not in urls_salvas]
        
        if not links_novos:
            print(f"    ✅ O ano {ano} já está completo no banco.")
            continue

        print(f"    🚀 Extraindo {len(links_novos)} jogos...")
        
        with concurrent.futures.ThreadPoolExecutor(THREADS_MAX) as executor:
            resultados = list(executor.map(extrair_dados_jogo, links_novos))
       
        lote_para_salvar = []
        data_ext = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for url, dados in zip(links_novos, resultados):
            if dados:
               
                jogo = (
                    url, 
                    dados['Título'], 
                    ano, 
                    dados['Gênero Principal'], 
                    dados['Plataforma Original'], 
                    dados['User Rating'], 
                    dados['Votos'], 
                    dados['Imagem'], 
                    dados['Link Download'], 
                    data_ext
                )
                lote_para_salvar.append(jogo)
                urls_salvas.add(url)

      
        if lote_para_salvar:
            cursor.executemany('''
                INSERT OR REPLACE INTO jogos 
                (url, titulo, ano, genero, plataforma, nota, votos, imagem_url, link_download, data_extracao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', lote_para_salvar)
            
          
            conexao.commit() 
            print(f"    💾 {len(lote_para_salvar)} jogos de {ano} salvos com sucesso!")

    conexao.close()
    print("\nPROCESSO FINALIZADO!")

if __name__ == '__main__':
    rodar_populador()