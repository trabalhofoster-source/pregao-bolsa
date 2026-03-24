import socket
import threading
import time
import os

conectado = False  
logado = False # pra validar o login do cliente

def formatar_e_imprimir(mensagem: str) -> None:
    mensagem = mensagem.strip()
    if not mensagem:
        return
    
    if '--- COTAÇÕES' in mensagem:
        tipo = '[FEED]'
    elif 'ERRO' in mensagem.upper():
        tipo = '[ALERTA]'
    else:
        tipo = '[RESPOSTA]'

    print(f"\n{tipo}\n{mensagem}")


def receber_mensagens(sock: socket.socket) -> None:
    global conectado
    global logado
    while conectado:
        try:
            dados:bytes = sock.recv(4096)
            if not dados:
                print("\n[INFO]\nConexão encerrada pelo servidor.")
                break
            mensagem = dados.decode(errors='ignore')

            if("OK" in mensagem):
                logado = True
                continue

            formatar_e_imprimir(mensagem)

        except OSError:
            break
        except Exception as e:
            print(f"\n[ALERTA]\nErro ao receber dados: {e}")
            break

    conectado = False

def menu_opcoes()->None:
    print("\nComandos disponíveis:")
    print("  :buy <ATIVO> <QTD>")
    print("  :sell <ATIVO> <QTD>")
    print("  :carteira")
    print("  :cotacao")
    print("  :exit (encerra a conexão)")
    print()

def encerrar_conexao(sock:socket.socket)->None:
    global conectado
    conectado = False
    try:
        sock.close()
    except OSError:
        pass
    print("Conexão encerrada pelo cliente.")

def comando_input()->str:
    comando:str = input("> ").strip()
    return comando

def enviar_comandos(sock: socket.socket) -> None:
    global conectado
    global logado

    while conectado:
        if(logado):
            menu_opcoes()
        try:
            comando = comando_input()
            if not comando:
                continue
            
            os.system('cls' if os.name == 'nt' else 'clear')
            if comando == ':exit':
                encerrar_conexao(sock)
                break
            
            sock.send((comando + "\n").encode())
        except (EOFError, KeyboardInterrupt):
            conectado = False
            try:
                sock.close()
            except OSError:
                pass
            print("\nConexão encerrada pelo cliente (interrupção).")
            break
        except OSError:
            break
        time.sleep(0.5)
        

def main():
    global conectado
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 50)
    print("CLIENTE - PREGÃO DA BOLSA DE VALORES")
    print("=" * 50)

    try:
        sock = socket.socket()
        sock.connect(('127.0.0.1', 12345))
    except Exception as e:
        print(f"Não foi possível conectar ao servidor: {e}")
        return

    conectado = True
    thread_receber = threading.Thread(target=receber_mensagens, args=(sock,), daemon=True)
    thread_receber.start()

    print("Siga as instruções na tela para Login ou Cadastro.")

    horario = time.strftime('%H:%M:%S')
    print(f"\n{horario}: CONECTADO!!")
    print("Aguardando cotações do servidor...\n")

    thread_receber = threading.Thread(
        target=receber_mensagens,
        args=(sock,),
        daemon=True
    )
    thread_receber.start()

    enviar_comandos(sock)


if __name__ == "__main__":
    main()

