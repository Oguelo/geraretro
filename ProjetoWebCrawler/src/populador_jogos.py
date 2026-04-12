import concurrent.futures
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from constants import ANOS_PROCESSO, LIMITE_PAGINAS, HEADERS, THREADS_MAX, BASE_URL
from database import obter_conexao, inicializar_banco
from scraper import extrair_dados_jogo

def buscar_links_do_ano(ano, session):
    links = []
    print(f" ano {ano}")
    
    pagina = 1
    while pagina <= LIMITE_PAGINAS:
        url = f"{BASE_URL}/browse/year/{ano}/" if pagina == 1 else f"{BASE_URL}/browse/year/{ano}/page/{pagina}/"
        print(f" página {pagina}...", end="\r") 
        
        try:
            res = session.get(url, timeout=15)
            
            if res.status_code == 404:
                break
            
            if res.status_code == 503:
                print(f"\n Erro 503 (Bloqueio)")
                time.sleep(20)
                continue

            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            tags = soup.find_all('a', class_='name')
            
            if not tags:
                break
                
            for t in tags:
                links.append(f"{BASE_URL}{t['href']}")
            
            pagina += 1
            time.sleep(1.5)
            
        except Exception as e:
            print(f"\n  Erro inesperado: {e}")
            break
            
    print(f"\n Total de links capturados: {len(links)}")
    return links

def rodar_populador():
    inicializar_banco()
    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT url FROM jogos")
    urls_salvas = {linha[0] for linha in cursor.fetchall()}
    
    with requests.Session() as session:
        session.headers.update(HEADERS) 
        
        for ano in ANOS_PROCESSO:
            print(f"\nPROCESSANDO ANO: {ano} ---")
            
            links_do_ano = buscar_links_do_ano(ano, session)
            links_novos = [l for l in links_do_ano if l not in urls_salvas]
            
            if not links_novos:
                continue
            
            print(f" Total para processar: {len(links_novos)} jogos.")
            
            tamanho_lote = 50 
            lotes_separados = [links_novos[i : i + tamanho_lote] for i in range(0, len(links_novos), tamanho_lote)]
            
            for num_lote, lote_links in enumerate(lotes_separados, start=1):
                print(f" Lote {num_lote}: Extraindo {len(lote_links)} jogos da web...")
                
                with concurrent.futures.ThreadPoolExecutor(THREADS_MAX) as executor:
                    futuros = [executor.submit(extrair_dados_jogo, url, session) for url in lote_links]
                    resultados = [futuro.result() for futuro in futuros]
                
                dados_para_salvar = []
                agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                for url, dados in zip(lote_links, resultados):
                    if dados:
                        dados_para_salvar.append((
                            url, dados['Título'], ano, dados['Gênero Principal'], 
                            dados['Plataforma Original'], dados['User Rating'], 
                            dados['Votos'], dados['Imagem'], dados['Link Download'], agora
                        ))

                if dados_para_salvar:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO jogos 
                        (url, titulo, ano, genero, plataforma, nota, votos, imagem_url, link_download, data_extracao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', dados_para_salvar)
                    
                    conexao.commit()
                    print(f" Lote {num_lote} salvo")
                    
                    for item in dados_para_salvar:
                        urls_salvas.add(item[0])

    conexao.close()
    print("\nFINALIZADO!")

if __name__ == '__main__':
    rodar_populador()