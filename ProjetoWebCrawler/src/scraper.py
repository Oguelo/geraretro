import requests
from bs4 import BeautifulSoup
import time
import random
from constants import HEADERS

def extrair_dados_jogo(url):
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        time.sleep(random.uniform(1.0, 3.0))
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 503:
                time.sleep(10)
                continue
            
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            dados = {
                'Título': 'Não encontrado',
                'Gênero Principal': 'Não encontrado',
                'Plataforma Original': 'Não encontrado',
                'User Rating': 0.0,
                'Votos': 0,
                'Imagem': 'Sem imagem',
                'Link Download': 'Não encontrado'
            }
    
            caixa_principal = soup.find('div', class_='box')
            if caixa_principal and caixa_principal.find('h2'):
                dados['Título'] = caixa_principal.find('h2').text.strip()
            
            tabela_info = soup.find('table', class_='gameInfo')
            if tabela_info:
                for linha in tabela_info.find_all('tr'):
                    th = linha.find('th')
                    td = linha.find('td')
                    if th and td:
                        txt = th.text.strip()
                        if txt == 'Genre': dados['Gênero Principal'] = td.text.strip()
                        elif txt == 'Platform': dados['Plataforma Original'] = td.text.strip()
            
            rating_box = soup.find('div', id='grRaB')
            if rating_box:
                spans = rating_box.find_all('span')
                if len(spans) >= 3:
                    dados['User Rating'] = float(spans[0].text.strip())
                    dados['Votos'] = int(spans[2].text.strip())
            
            img = soup.find('meta', property='og:image')
            if img: dados['Imagem'] = img['content']
            
            for a in soup.find_all('a', href=True):
                if '/download/' in a['href']:
                    dados['Link Download'] = f"https://www.myabandonware.com{a['href']}"
                    break
            
            return dados
        except:
            if tentativa == max_tentativas - 1: return None
            time.sleep(5)
    return None