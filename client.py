import socket
import threading
import time
import os

conectado = False


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
    print(f"\n{horario}: CONECTADO!!\n")

    try:
        dados = sock.recv(1024)
        if dados:
            mensagem = dados.decode(errors='ignore')
            formatar_e_imprimir(mensagem)
    except Exception as e:
        print(f"\n[ALERTA]\nErro ao receber: {e}")

    input("\nPressione ENTER para continuar... ")

    try:
        sock.send("\n".encode())
    except OSError:
        pass

    sock.close()
    conectado = False
    print("\n[INFO]\nConexão encerrada.")


if __name__ == "__main__":
    main()
