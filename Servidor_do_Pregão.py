import socket
import threading
import random
import time
import os

servidor_socket = None
servidor_ativo = False

preco_acoes = {
    'SANB11': 20.0,
    'BBAS3': 20.0,
    'BBDC4': 20.0,
    'ITUB4': 20.0
}

carteira_clientes = {}
clientes_conectados = []

def gerar_mensagem_cotacoes():
    mensagem = f"\n--- COTAÇÕES {time.strftime('%H:%M:%S')} ---\n"
    for acao, preco in preco_acoes.items():
        mensagem += f"{acao}: R$ {preco:.2f}\n"
    return mensagem

def atualizar_cotacoes():
    global preco_acoes
    while servidor_ativo:
        for acao in preco_acoes:
            variacao = round(random.uniform(-1.0, 1.0), 2)
            novo_preco = preco_acoes[acao] + variacao
            preco_acoes[acao] = max(10.0, min(30.0, round(novo_preco, 2)))
        time.sleep(15)

def processar_cliente(conexao, endereco):
    if endereco not in carteira_clientes:
        carteira_clientes[endereco] = {
            'saldo': 10000.0,
            'ativos': {acao: 0 for acao in preco_acoes}
        }
    
    dados_cliente = carteira_clientes[endereco]
    
    while True:
        try:
            comando = conexao.recv(1024).decode().strip()
            if not comando:
                break
                
            partes = comando.split()
            
            if partes[0] == ':buy' and len(partes) == 3:
                acao = partes[1].upper()
                try:
                    quantidade = int(partes[2])
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

                    mensagem = (
                        f'Compra realizada: {quantidade} {acao} '
                        f'a R$ {preco_unitario:.2f} (total R$ {valor_total:.2f})\n'
                    )
                    conexao.send(mensagem.encode())
                    
            elif partes[0] == ':sell' and len(partes) == 3:
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

                    conexao.send(f'Venda realizada: {quantidade} {acao}\n'.encode())
                    
            elif comando == ':carteira':
                resposta = f"Saldo: R$ {dados_cliente['saldo']:.2f}\n"
                for acao, qtd in dados_cliente['ativos'].items():
                    if qtd > 0:
                        valor_total = preco_acoes[acao] * qtd
                        resposta += f"{acao}: {qtd} = R$ {valor_total:.2f}\n"
                conexao.send(resposta.encode())
            
            elif comando == ':cotacao':
                mensagem = gerar_mensagem_cotacoes()
                conexao.send(mensagem.encode())
                
            else:
                conexao.send(b'Comando invalido\n')
                
        except:
            break
    
    conexao.close()
    if (conexao, endereco) in clientes_conectados:
        clientes_conectados.remove((conexao, endereco))
        n = len(clientes_conectados)
        print(f"\rCliente {endereco} saiu. Clientes conectados: {n}                    \nEscolha: ", end="")

def servidor_principal():
    global servidor_socket

    servidor_socket = socket.socket()
    servidor_socket.bind(('127.0.0.1', 12345))
    servidor_socket.listen(5)

    print("Servidor aguardando conexões...\n")
    
    while servidor_ativo:
        try:
            servidor_socket.settimeout(1)
            conexao, endereco = servidor_socket.accept()
            clientes_conectados.append((conexao, endereco))
            n = len(clientes_conectados)
            print(f"\rCliente {endereco} conectado. Clientes conectados: {n}                    \nEscolha: ", end="")

            thread_cliente = threading.Thread(
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

def menu_principal():
    global servidor_ativo, servidor_socket
    os.system('cls' if os.name == 'nt' else 'clear')
    terminar_servidor()
    while True:
        opcao = input("Escolha: ")
        
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
            print("Programa encerrado!")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu_principal()