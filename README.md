# pregao-bolsa
## Sobre
    Pregao-bolsa é um programa que simula o acesso às bolsas de valores e saldo bancário, podendo:
        - acessar ao saldo disponível (":carteira")
        - ver ações (:cotacao)
        - comprar uma cota (:buy <ATIVO> <QTD>)
        - vende ação (:sell <ATIVO> <QTD>)
        - sair do programa (:exit)
    
    Para iniciar o programa, o arquivo Servidor_do_Pregão.py deverá ser inicializado antes de client.py, caso contrário aparecerá um aviso de "Não foi possível conectar ao servidor".
    Tendo inciado o Servidor_do_Pregão.py, é preciso eleger uma de três funções, pondendo somente ser o número digitado:
        - 1 - LIGAR SERVIDOR
        - 2 - DESLIGAR SERVIDOR
        - 3 - SAIR
    O primeiro, permitindo conexão ao client.py, o segundo barrando essa conexão e o último parando o programa.

    Escolhida a opção 1, a seguinte tela aparecerá:
        - :buy <ATIVO> <QTD>
        - :sell <ATIVO> <QTD>
        - :carteira
        - :cotacao
        - :exit (encerra a conexão)
    Note que deve ser escrito com os ":" no início.
    Selecionando a opção ":carteira", ele retornará o quanto ainda se tem de saldo (sendo o saldo inicial R$10000), se gasto com alguma cotação ou se alguma contação vendida, isso mudará o valor disponível.
    Agora, escolhendo ":cotacao", a tela em que mostra quanto está cada ação é atualizada a cada 5 segundos, aparecendo as opções disponíveis e seus respectivos preços, exemplo:
        --- COTAÇÕES 19:49:11 ---
        - (atualizações a cada 5s) -
        SANB11: R$ 21.60
        BBAS3: R$ 14.31
        BBDC4: R$ 25.22
        ITUB4: R$ 19.04
        PETR4: R$ 24.80
        VALE3: R$ 24.57
        MGLU3: R$ 18.03
    Perceba que aparece, logo quando se mostra a cotação, o horário em que houve a volatilidade do preço, além dos nomes das ações à esquerda e seus preçoos à direita.
    Sabendo dos preços e do saldo disponível, podemos fazer a compra de uma ação com mais segurança, selecionando quantas cotas deseja, o program retornará isto: 
        - Compra realizada: 4 PETR4 a R$ 27.69 (total R$ 110.76)
    Sendo esse 4 inicial a quantidade comprada e o valor final o quanto foi gasto ao todo.
    Como os preços são voláteis, é possível vendê-las, podendo ter um lucro ou perda sobre as vendas. Isso é possível através da função :sell <ATIVO> <QTD>. Digitado isso, isto deverá aparecer no log:
        - Venda realizada: 4 PETR4
    Por fim, querendo sair do programa client.py, é necessário digita ":exit" que o programa será finalizado, e mostrado no log "Conexão encerrada pelo cliente.".

## Bibliotecas
    Bibliotecas utilizadas:
        - socket
        - threading
        - time
        - os
        - random