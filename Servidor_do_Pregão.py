import socket
import threading
import random
import time
import os
import json

servidor_socket = None
servidor_ativo = False
lock_json = threading.Lock()

DIRETORIO_CARTEIRAS = 'carteiras_clientes'

MAX_CLIENTES = 2
clientes_ativos = 0
lock_clientes = threading.Lock()

def _caminho_json_cliente()->str:
    if not os.path.exists(DIRETORIO_CARTEIRAS):
        os.makedirs(DIRETORIO_CARTEIRAS, exist_ok=True)
    return os.path.join(DIRETORIO_CARTEIRAS, f"clientes.json")

##################
#### CADASTRO ####
##################

def criar_login(conexao:socket.socket)->None:
    conexao.send(b"Digite seu email: ")
    email:str = conexao.recv(1024).decode().strip()
    while(True):
        conexao.send(b"Digite uma senha: ")
        senha:str = conexao.recv(1024).decode().strip()
        conexao.send(b"Confirme sua senha: ")
        segunda_senha:str = conexao.recv(1024).decode().strip()
        if(senha != segunda_senha):
            conexao.send("As senhas nao conferem".encode())
            continue
        else:
            break

    caminho = _caminho_json_cliente()
    if(os.path.exists(caminho)):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                if conteudo.strip():
                    clientes = json.loads(conteudo)
                else:
                    clientes = {}
        except json.JSONDecodeError:
            print("Aviso: Arquivo JSON corrompido ou vazio. Reiniciando base.")
            clientes = {}
    else:
        clientes = {}
    
    if(email in clientes):
        conexao.send("Este email já existe".encode())
        return

    clientes[email] = {
        "senha":senha, 
        "saldo": 1000.0, 
        'ativos': {acao: 0 for acao in preco_acoes}
    }

    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(clientes, f, ensure_ascii=False, indent=4)

preco_acoes:dict[str, float] = {
    'SANB11': 20.0,
    'BBAS3': 20.0,
    'BBDC4': 20.0,
    'ITUB4': 20.0,
    'PETR4': 20.0,
    'VALE3': 20.0,
    'MGLU3': 20.0
}

# Agora a carteira é persistida via JSON de cada cliente
# carteira_clientes:dict[str, dict[str, float|dict[str, int]]] = {}
clientes_conectados:list[tuple[str,str]] = []


def carregar_carteira(endereco:str)->None|dict[str,str]:
    caminho:str = _caminho_json_cliente(endereco)
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def salvar_carteira(email, novos_dados_cliente):
    with lock_json:
        caminho = _caminho_json_cliente()
        with open(caminho, 'r', encoding='utf-8') as f:
            todos_clientes = json.load(f)
        todos_clientes[email].update(novos_dados_cliente)

        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(todos_clientes, f, ensure_ascii=False, indent=4)

att_cotacoes:bool = False
def gerar_mensagem_cotacoes(conexao:socket.socket)->None:
    global att_cotacoes
    att_cotacoes = True
    count:int = 0
    while(att_cotacoes):
        if(count%5==0):
            mensagem:str = f"\n--- COTAÇÕES {time.strftime('%H:%M:%S')} ---\n - (atualizações a cada 5s) -\n"
        else:
            mensagem:str = f"\n--- COTAÇÕES {time.strftime('%H:%M:%S')} ---\n"
        for acao, preco in preco_acoes.items():
            mensagem += f"{acao}: R$ {preco:.2f}\n"
        conexao.send(mensagem.encode())
        time.sleep(5)
        count+=1
        

def atualizar_cotacoes()->None:
    global preco_acoes
    while servidor_ativo:
        for acao in preco_acoes:
            variacao:float = round(random.uniform(-1.0, 1.0), 2)
            novo_preco:float = preco_acoes[acao] + variacao
            preco_acoes[acao] = max(10.0, min(30.0, round(novo_preco, 2)))
        time.sleep(2)

def processar_cliente(conexao:socket.socket, endereco:str)->None:
    global att_cotacoes

    email_usuario = None
    dados_cliente = ""
    clientes = {}
    mensagem:str = f'{"="*20} MENU {"="*20}'
    conexao.send(mensagem.encode())
    while not email_usuario:
        conexao.send(b"Possui uma conta? (s/n) ou 'sair':")
        resposta:str = conexao.recv(1024).decode().strip()

        if(resposta in ['n', 'nao', 'não', 'noa']):
            criar_login(conexao)
        elif(resposta in ['s', 'sim', 'si', 'sin', 'smi', 'msi', 'mis']):
            conexao.send(b"Digite seu email: ")
            email = conexao.recv(1024).decode().strip()
            conexao.send(b"Digite sua senha: ")
            senha = conexao.recv(1024).decode().strip()
            caminho = _caminho_json_cliente()

            if os.path.exists(caminho):
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                        if conteudo.strip():
                            clientes = json.loads(conteudo)
                        else:
                            clientes = {}
                    if(email in clientes and clientes[email]['senha'] == senha):
                        email_usuario = email
                        dados_cliente = clientes[email_usuario]
                        conexao.send(b"\t===LOGIN FETUADO COM SUCESSO===\n")
                        time.sleep(1)
                        conexao.send(b"OK")
                        conexao.send("*Aperte ENTER para continuar".encode())
                        # soh roda o loop das cotacoes quando o login for executado
                        loop_cotacoes = threading.Thread(target=gerar_mensagem_cotacoes, args=(conexao,), daemon=True)
                    else:
                        conexao.send(b"Email ou senha invalidos. Tente novamente\n")        
                except json.JSONDecodeError:
                    print("Aviso: Arquivo JSON corrompido ou vazio. Reiniciando base.")
                    clientes = {}
            else:
                conexao.send(b"Nenhum usuario cadastrado no sistem.\n")
                clientes = {}

        elif(resposta in ['sair', 'sir', 'exit', 'esit', 'eksit', 'equisit']):
            conexao.send(f"{'='*25} SESSAO ABORTADA {'='*25}".encode())
            with lock_clientes:
                clientes_ativos -= 1
            conexao.close()            
        else:
            mensagem:str = "Comando não reconhecido"
            conexao.send(mensagem.encode())

    while True:
        try:
            comando:str = conexao.recv(1024).decode().strip()
            if not comando:
                break
            partes:list[str] = comando.split()
            
            if partes[0] == ':buy' and len(partes) == 3:
                if(att_cotacoes):
                    att_cotacoes = False
                    time.sleep(5)
                acao = partes[1].upper()
                try:
                    quantidade:int = int(partes[2])
                except ValueError:
                    conexao.send(b'ERRO: Quantidade invalida\n')
                    continue
                
                if acao not in preco_acoes:
                    conexao.send(b'ERRO: Acao nao encontrada\n')
                elif dados_cliente['saldo'] < preco_acoes[acao] * quantidade:
                    conexao.send(b'ERRO: Saldo insuficiente\n')
                else:
                    preco_unitario = preco_acoes[acao]
                    valor_total = preco_unitario * quantidade
                    dados_cliente['saldo'] -= valor_total
                    dados_cliente['ativos'][acao] += quantidade
                    salvar_carteira(email_usuario, dados_cliente)

                    mensagem:str = (
                        f'Compra realizada: {quantidade} {acao} '
                        f'a R$ {preco_unitario:.2f} (total R$ {valor_total:.2f})\n'
                    )
                    conexao.send(mensagem.encode())
                    
            elif partes[0] == ':sell' and len(partes) == 3:
                if(att_cotacoes):
                    att_cotacoes = False
                    time.sleep(5)
                acao = partes[1].upper()
                try:
                    quantidade = int(partes[2])
                except ValueError:
                    conexao.send(b'ERRO: Quantidade invalida\n')
                    continue
                
                if dados_cliente['ativos'][acao] < quantidade:
                    conexao.send(b'ERRO: Quantidade insuficiente\n')
                else:
                    dados_cliente['saldo'] += preco_acoes[acao] * quantidade
                    dados_cliente['ativos'][acao] -= quantidade
                    salvar_carteira(email_usuario, dados_cliente)

                    conexao.send(f'Venda realizada: {quantidade} {acao}\n'.encode())
                    
            elif comando == ':carteira':
                if(att_cotacoes):
                    att_cotacoes = False
                    time.sleep(5)
                resposta:str = f"Saldo: R$ {dados_cliente['saldo']:.2f}\n"
                for acao, qtd in dados_cliente['ativos'].items():
                    if qtd > 0:
                        valor_total:int|float = preco_acoes[acao] * qtd
                        resposta += f"{acao}: {qtd} = R$ {valor_total:.2f}\n"
                conexao.send(resposta.encode())
            
            elif comando == ':cotacao':
                loop_cotacoes.start()
                
            else:
                if(att_cotacoes):
                    att_cotacoes = False
                    time.sleep(5)
                conexao.send(b'Comando invalido\n')
        except:
            break
    
    salvar_carteira(email_usuario, dados_cliente)
    conexao.close()
    with lock_clientes:
        clientes_ativos -= 1
    if (conexao, endereco) in clientes_conectados:
        clientes_conectados.remove((conexao, endereco))
        n:int = len(clientes_conectados)
        print(f"\rCliente {endereco} saiu. Clientes conectados: {n}                    \nEscolha: ", end="")

def servidor_principal()->None:
    global servidor_socket

    servidor_socket = socket.socket()
    servidor_socket.bind(('127.0.0.1', 12345))
    servidor_socket.listen(5)

    print("Servidor aguardando conexões...\n")
    
    while servidor_ativo:
        try:
            servidor_socket.settimeout(1)
            conexao, endereco = servidor_socket.accept()

            with lock_clientes:
                if clientes_ativos >= MAX_CLIENTES:
                    conexao.send(b"Servidor cheio. Maximo 2 clientes.\n")
                    conexao.close()
                    continue
                clientes_ativos += 1

            clientes_conectados.append((conexao, endereco))
            n = len(clientes_conectados)
            print(f"\rCliente {endereco} conectado. Clientes conectados: {n}                    \nEscolha: ", end="")

            thread_cliente:threading.Thread = threading.Thread(
                target=processar_cliente, 
                args=(conexao, endereco),
                daemon=True
            )
            thread_cliente.start()
        except:
            pass

def terminar_servidor():
    print("=" * 50)
    print("SERVIDOR DA BOLSA DE VALORES")
    print("=" * 50)
    print("1 - LIGAR SERVIDOR")
    print("2 - DESLIGAR SERVIDOR")
    print("3 - SAIR")
    print("=" * 50)

def menu_principal()->None:
    global servidor_ativo, servidor_socket
    os.system('cls' if os.name == 'nt' else 'clear')
    terminar_servidor()
    while True:
        opcao:str = input("Escolha: ")
        
        if opcao == '1' and not servidor_ativo:
            servidor_ativo = True
            os.system('cls' if os.name == 'nt' else 'clear')
            terminar_servidor()

            threading.Thread(target=atualizar_cotacoes, daemon=True).start()
            threading.Thread(target=servidor_principal, daemon=True).start()

            print("Servidor iniciado!\n")
            time.sleep(2)
            
        elif opcao == '2' and servidor_ativo:
            servidor_ativo = False
            os.system('cls' if os.name == 'nt' else 'clear')
            terminar_servidor()
            if servidor_socket:
                servidor_socket.close()
            print("Servidor desligado!\n")
            time.sleep(2)
            
        elif opcao == '3':
            if servidor_ativo:
                servidor_ativo = False
                if servidor_socket:
                    servidor_socket.close()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Programa encerrado!")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nAVISO: Interrupção por teclado detectada")
        print("AVISO: Desligando servidor", end="")
        for i in range(random.randint(4, 6)):
            print(end='.')
            time.sleep(random.uniform(0.5,1.5))
        if servidor_socket:
            servidor_socket.close()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        fim:str = "AVISO: Servidor desligado"
        print(f"\n{fim}")
        print("="*(len(fim)))
        print("\n"*20)