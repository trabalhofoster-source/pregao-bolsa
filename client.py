import os
import queue
import socket
import sys
import threading
import time

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

conectado = False
logado = False  # pra validar o login do cliente

fila_mensagens: "queue.Queue[str | None]" = queue.Queue()


def formatar_e_imprimir(mensagem: str) -> None:
    mensagem = mensagem.strip()
    if not mensagem:
        return

    if "--- COTAÇÕES" in mensagem:
        tipo = "[FEED]"
    elif "ERRO" in mensagem.upper():
        tipo = "[ALERTA]"
    else:
        tipo = "[RESPOSTA]"

    print(f"\n{tipo}\n{mensagem}")


def _largura_terminal_saida() -> int:
    try:
        return os.get_terminal_size(sys.stdout.fileno()).columns
    except OSError:
        return 120


def _limpar_linha_digitacao() -> None:
    cols = _largura_terminal_saida()
    sys.stdout.write("\r" + " " * cols + "\r")
    sys.stdout.flush()


def _imprimir_mensagem_servidor(mensagem: str, buffer: list[str]) -> None:
    s = "".join(buffer)
    _limpar_linha_digitacao()
    formatar_e_imprimir(mensagem)
    sys.stdout.write("> " + s)
    sys.stdout.flush()


def _drenar_fila(fila: "queue.Queue[str | None]", buffer: list[str]) -> bool:
    while True:
        try:
            item = fila.get_nowait()
        except queue.Empty:
            break
        if item is None:
            return True
        _imprimir_mensagem_servidor(item, buffer)
    return False


def _ler_linha_windows(fila: "queue.Queue[str | None]") -> str | None:
    buffer: list[str] = []
    sys.stdout.write("> ")
    sys.stdout.flush()
    while conectado:
        if _drenar_fila(fila, buffer):
            sys.stdout.write("\n")
            return None
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                msvcrt.getwch()
                continue
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buffer).strip()
            if ch in ("\x08", "\x7f"):
                if buffer:
                    buffer.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if ch == "\x03":
                raise KeyboardInterrupt
            if len(ch) == 1 and ch.isprintable():
                buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
        else:
            time.sleep(0.02)
    return None


def _ler_linha_unix(fila: "queue.Queue[str | None]") -> str | None:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buffer: list[str] = []
    sys.stdout.write("> ")
    sys.stdout.flush()
    try:
        tty.setcbreak(fd)
        while conectado:
            if _drenar_fila(fila, buffer):
                sys.stdout.write("\n")
                return None
            r, _, _ = select.select([fd], [], [], 0.05)
            if not r:
                continue
            chb = os.read(fd, 1)
            if not chb:
                return None
            ch = chb.decode("utf-8", errors="replace")
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buffer).strip()
            if ch in ("\x08", "\x7f"):
                if buffer:
                    buffer.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x04":
                return None
            if len(ch) == 1 and ch.isprintable():
                buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def ler_linha(fila: "queue.Queue[str | None]") -> str | None:
    if os.name == "nt":
        return _ler_linha_windows(fila)
    return _ler_linha_unix(fila)


def receber_mensagens(sock: socket.socket, fila: "queue.Queue[str | None]") -> None:
    global conectado, logado
    try:
        while conectado:
            try:
                dados: bytes = sock.recv(4096)
                if not dados:
                    print("\n[INFO]\nConexão encerrada pelo servidor.")
                    break
                mensagem = dados.decode(errors="ignore")

                if "OK" in mensagem:
                    logado = True
                    continue

                fila.put(mensagem)

            except OSError:
                break
            except Exception as e:
                print(f"\n[ALERTA]\nErro ao receber dados: {e}")
                break
    finally:
        conectado = False
        try:
            fila.put_nowait(None)
        except queue.Full:
            pass


def menu_opcoes() -> None:
    print("\nComandos disponíveis:")
    print("  :buy <ATIVO> <QTD>")
    print("  :sell <ATIVO> <QTD>")
    print("  :carteira")
    print("  :cotacao")
    print("  :exit (encerra a conexão)")
    print()


def encerrar_conexao(sock: socket.socket) -> None:
    global conectado
    conectado = False
    try:
        sock.close()
    except OSError:
        pass
    print("Conexão encerrada pelo cliente.")


def enviar_comandos(sock: socket.socket) -> None:
    global conectado

    while conectado:
        if logado:
            menu_opcoes()
        try:
            comando = ler_linha(fila_mensagens)
            if comando is None:
                break
            if not comando:
                continue

            os.system("cls" if os.name == "nt" else "clear")
            if comando == ":exit":
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


def main() -> None:
    global conectado, fila_mensagens

    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 50)
    print("CLIENTE - PREGÃO DA BOLSA DE VALORES")
    print("=" * 50)

    try:
        sock = socket.socket()
        sock.connect(("127.0.0.1", 12345))
    except Exception as e:
        print(f"Não foi possível conectar ao servidor: {e}")
        return

    fila_mensagens = queue.Queue()
    conectado = True

    horario = time.strftime("%H:%M:%S")
    print(f"\n{horario}: CONECTADO!!")

    print("Siga as instruções na tela para Login ou Cadastro.")

    thread_receber = threading.Thread(
        target=receber_mensagens, args=(sock, fila_mensagens), daemon=True
    )
    thread_receber.start()

    enviar_comandos(sock)


if __name__ == "__main__":
    main()
