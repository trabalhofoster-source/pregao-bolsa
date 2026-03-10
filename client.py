import socket
import threading
import time
import os

conectado = False


def formatar_e_imprimir(mensagem: str) -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    mensagem:str = mensagem.strip()
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
    while conectado:
        try:
            dados:bytes = sock.recv(4096)
            if not dados:
                print("\n[INFO]\nConexão encerrada pelo servidor.")
                break
            mensagem = dados.decode(errors='ignore')
            formatar_e_imprimir(mensagem)
        except OSError:
            break
        except Exception as e:
            print(f"\n[ALERTA]\nErro ao receber dados: {e}")
            break

    conectado = False

def menu_opcoes()->None:
    print("Comandos disponíveis:")
    print("  :menu")
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

def enviar_comandos(sock: socket.socket) -> None:
    global conectado
    menu_opcoes()

    while conectado:
        try:
            comando = input("> ").strip()
            if not comando:
                continue

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

