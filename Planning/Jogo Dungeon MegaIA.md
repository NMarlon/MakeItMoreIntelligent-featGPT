

 


 # Modelo 

## Técnica Manual de Desenvolvimento para Planejamento - Resultado Esperado Final
*(se fosse fazer na mão cada passo do que a IA deveria fazer até o fim, como seria?)*
- Ver (Sensores) 👀
- Quando tiver a oportunidade Atacar o Monstro (isso é válido pra todo trajeto depois de (Ver (Sensores))) 🤺
    - (A* no monstro e ataque)
    - Senão vai fugir do Monstro
- Ele vai procurar a planta (vasculhar cenário, partes aonde ainda não viu) 🔎🍎 
    - não vai cair no buraco
    - Nem cair no monstro
- Vai guardar na memória onde já viu (pra não ir de novo) 🗺️
- Quando encontrar vai Traçar caminho pra Planta desviando dos buracos 🚶🏻‍♀️🕳️





## O que a IA VAI ser para ser IA?
*Partindo da Técnica manual*
### Preparação Inicial
- Irá receber treinamento das regras e fundamentos desse jogo (situação 1)
- NÃO irá receber treinamento e regras explícitas do jogo (situação 2)


### Em jogo
- Ver (Sensores)
- Reconhecer na memória a SITUAÇÃO
    1. De preferência, Deve distinguir cenários diferentes. (Não confundir um cenário com outro que passou)
    2. Testar a memória (coisa da IA)
- Atualizar memória
- Pensar nas possibilidades
    1. Se for considerado impossível pelo Bot
        1. Ele pode, infelizmente, acabar se contentar com o que sabe e não agir (X), ou 
        2. Vasculhar (Curiosidade) (<-)
- Agir de acordo com a memória (se houver)
- 