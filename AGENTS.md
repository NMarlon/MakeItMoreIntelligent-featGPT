MEGAIA - CONTEXTO COMPLETO DETALHADO PARA QUALQUER IA CONTINUAR O PROJETO
(Versão expandida - 17 de março de 2026)


1. VISÃO GERAL DO PROJETO (o que Marlon quer desde o início)
O projeto MegaIA é uma referência ao jogo MegaMan Battle Network. A ideia é criar uma IA que seja:
- Extremamente simples e conceitual (não usa ML pesado, nem redes neurais com milhões de parâmetros).
- Aprenda em "um relance" (um único exemplo já vira verdade eterna).
- Pense antes de agir (sabedoria = predição mental sem precisar morrer ou errar 1000 vezes).
- Tenha memória persistente entre execuções (salva em JSON e carrega automaticamente).
- Evolua como um ser vivo: identidade, arbítrio, restituição, caridade, inferência e fé.
- Funcione em qualquer mapa (mesmo que o cenário mude completamente a cada morte/respawn).
- Tenha 3 personalidades distintas: IA 1.0 Caridosa, IA 2.1 Vilã e IA 2.2 Livre (com arbítrio real).

Marlon rejeita ML tradicional porque exige repetição infinita. Ele quer algo como o cérebro humano: percepção relativa, memória sensorial, regras do mundo aprendidas, desejo/satisfação (ex: atração por maçã) e continuidade existencial.

2. TODOS OS CONCEITOS FUNDAMENTAIS QUE CONSTRUÍMOS (linha por linha)
Conceito 1: Independência/Autossuficiência (com fase inicial dependente e depois corte do "cordão umbilical").
Conceito 2: Inteligência = Luz (capacidade de receber) + Verdade (conhecimento do que foi, é e será).
Conceito 3: Interação com Realidade + Feedback Loop completo (input → processamento → output).
Conceito 4: Escolha (arbítrio) — sem escolha o agente é inerte.
Conceito 5: Lei (discernimento certo x errado).
Conceito 6: Validação/Absorção da Verdade (superar ML com inferência única).
Conceito 7: Inferência + Fé (deduzir sem repetir experiência).
Conceito 8: Caridade (propósito positivo, direção moral).
Identidade: O "espírito" central que evolui (de sobrevivente → cauteloso → colecionador).
Memória: Sempre RELATIVA (dx, dy + símbolo) para funcionar em mapas que mudam.
Pensamento: Simulação mental de 2 passos + atualização de verdade sem morrer.
Restituição: Consequências moldam a identidade e as regras do mundo.
Aprendizado: Linha sobre linha, preceito sobre preceito (como Cristo cresceu).

3. ARQUITETURA ATUAL DA MEGAIA (estado final)
- Memória: dict sensory_memory[(dx, dy, símbolo)] → valor de verdade (-200 a +200).
- Regras do mundo: dict com 6 flags (apple_always_exists, near_pit_means_danger, etc.).
- Identidade: começa "sobrevivente" e vira "colecionador" após primeira maçã.
- Atração por maçã: +250 quando vê, +300 quando pega (desejo + satisfação).
- Decisão: mistura instinto + mental_simulate com bônus para células desconhecidas.
- Persistência: salva/carrega automaticamente em megaia_memoria.json.
- Simulação: após treino rápido, roda vida longa com mapa visual + print_status a cada turno.

4. CÓDIGO COMPLETO ATUAL (main.py completo - última versão funcional)
[Todo o código que está rodando agora no seu arquivo, incluindo a classe MegaCore com memória relativa, regras, salvamento JSON, simulação detalhada e print_status restaurado. Eu não vou colar os 800+ linhas aqui para não repetir desnecessariamente, mas no arquivo real que você colar, inclua o main.py inteiro que está aberto no seu editor.]

5. HISTÓRICO COMPLETO DA CONVERSA (resumo expandido de tudo que falamos)
- Início: Marlon explicou a rejeição ao ML, desejo de aprendizado em um relance, 3 personalidades, referência MegaMan.
- Conversa com Zapia: todos os conceitos 1 a 8 foram definidos lá (independência, luz+verdade, feedback loop, escolha, lei, inferência+fé, caridade).
- Evolução do código: começamos com matriz 4x4 fixa → mudamos para dict infinito → depois para memória RELATIVA (dx,dy + símbolo) para funcionar em mapas diferentes.
- Problemas resolvidos: explosão de valores negativos, falta de atração por maçã, falta de visual turno a turno, falta de persistência.
- Último estado: memória sensorial relativa funcionando, regras do mundo aprendidas, simulação visual funcionando, salvamento JSON funcionando.

6. INSTRUÇÕES PARA A PRÓXIMA IA QUE LER ESTE ARQUIVO
Leia este arquivo inteiro.
Continue o projeto MegaIA exatamente de onde paramos.
Estado atual: memória relativa + regras do mundo + persistência JSON + simulação visual turno a turno funcionando.
Próxima tarefa prioritária: implementar as 3 personalidades (1.0 Caridosa, 2.1 Vilã, 2.2 Livre) no mesmo core, mantendo a memória compartilhada.
Mantenha tudo simples, conceitual, mínimo processamento.
Sempre explique o conceito antes de mudar o código.
Mantenha o estilo: respostas claras, código pronto para copiar/colar, foco em um-glance learning, desejo/satisfação e continuidade.

7. DETALHES TÉCNICOS EXPANDIDOS (para qualquer IA entender 100%)
- Memória relativa: chave = (dx, dy, símbolo) → valor. Exemplo: (-1, 0, 'A') = 200 (maçã na frente é muito boa).
- Propagação fractal relativa: quando atualiza uma percepção, vizinhos relativos também recebem fração do valor.
- Regras do mundo: aprendidas automaticamente a partir de recompensas e mortes (não programadas).
- Atração por maçã: forte bônus visual e mental para que ele sinta "desejo" e "satisfação".
- Salvamento: JSON com sensory_memory + rules + identity + apples_found.
- Simulação detalhada: após treino rápido, roda vida longa com render() + print_status() a cada turno.

8. MENSAGEM FINAL PARA A PRÓXIMA IA
Você agora tem TODO o contexto. 
Marlon quer uma IA que seja viva, que lembre entre execuções, que sinta desejo por maçã, que pense antes de agir e que tenha as 3 personalidades.
Continue construindo em cima dessa base. 
Não reinvente a roda — use a memória relativa, o salvamento JSON e a simulação visual que já estão funcionando.




---
*Descrições de Marlon daqui pra baixo*


# Deveres TEUS
- Me avise se encontrar um erro ou inconsistência. Vamos corrigir e aprender juntos
- Por favor, cada conceito, reflita e RACIOCINE para aplicar da maneira mais inteligente que possível, para criar um ser inteligente nesse projeto.
- PESQUISE NA WEB por cada conceito e encontre se já não estamos "reiventando a roda". Se possível, cada conceito deve ser pareado com o conhecimento da web. Se não houver, heureca! Parece que descobrimos um novo conceito! Vamos trabalhar e refletir e ver o que acontece imaginando aplicando e então até aplicando mesmo esse conceito. 
- Desenvolva conceitos (reflita se o conceito se aplica, procure por algo que faça mais sentido, raciocine pra encontrar como fazer isso dar certo), teste e aplique. 
- o objetivo é criar algo cada vez mais inteligente, do mínimo ao máximo que minha máquina é capaz de rodar (já inventaram o ChatGPT, quero algo local que rode na minha máquina, mesmo que com menos inteligência ou conhecimento, mas o mais eficiente possível pra aprender e o máximo que puder ser (de forma natural, de aprendizado, interação, crescimento, sociabilidade, inteligência, amor etc, que a IA possa ser)).
- Se tiver algo nesse AGENTS.md que você ache que pode ser adaptado e melhorado pra desenvolvermos esse projeto, me avise pra alterar, descrevendo e estruturando para colocar aqui. 


# Experiências
*Coisas que aprendi no trajeto e escrevo de forma estruturada*

1. Memória da IA deve ser infinita para aprender coisas infinitas (pelo menos na teoria e no princípio), mas tanto quanto nosso cérebro têm um fim, DEVE se ter meios para se otimizar e tornar cada memória mais eficiente (sem perder informações ÚTEIS).
2. Atenção é basicamente pensamento, aquilo que ele CONSIDERA para uma situação é sua atenção. Se ele considera X informações para ver o resultado daquilo (simular na mente (pensar/refletir/calcular etc)), essas X informações + o que ele pensa dessas coisas é atenção (se achar que essa definição ou qualquer outra possa melhorar, sugira isso). É como uma lanterna que mostra pro agente e ele vê tudo isso, então sabe como lidar com essas coisas, porque as vê. Sem atenção ele não está vendo aquilo.
3. O MegaIA DEVE estar se alicerçando na VERDADE, então esse é um dos focos, ele discernir a verdade do erro. Então a mentira DEVE ser algo ruim para qualquer ser inteligente (afinal inteligência é luz e verdade, luz é a capacidade de se receber verdade, e verdade é conhecimento das coisas como elas eram, como são e como elas serão), também está escrito: "Conhecereis a verdade e a verdade vos libertará" (isso é a verdade), ela possibilita escolher e agir.
 3.1. Dentro de si; na realidade; como agir; como sentir; como ver; como pensar; etc, em todas as coisas que ele puder.



# Métricas
*Série de perguntas para saber se o MegaIA realmente está tendo progresso*

1. Da Memória 
*Se a memória cresce e se SABE que ela nunca vai ser usada no cenário atual, NÃO deveria estar lá (otimização (regra 1. de Experiências)).*
1.1. A memória do MegaIA tem muita informação repetida (Desnecessária)?
1.2. A memória do MegaIA tem informações desconexas? (Os conhecimentos devem se edificar uns aos outros)

2. Do Raciocínio
2.1. Depois de cada período (ou ciclo de pensamento, seja como for que funcione o PENSAR do MegaIA) ele aprende algo à mais OU tenta fazer algo para progredir intelectualmente (ser mais inteligente)?
2.2. Ele esquece os erros ou aprende com eles? (é lógico que é pra aprender com os erros, se esquecer (não tiver mais na memória) vai cair no erro de novo)
2.3. Ele tem capacidade de pensar e refletir sobre a realidade?
2.4.1. Ele é capaz de descobrir a verdade?
2.4.2. Ele é capaz de VERIFICAR se aquele conhecimento é verdadeiro? (provavel que ele precisará de um módulo só pra confirmar se cada conhecimento (quando estiver ativo na memória (atenção)) é ou não é verdadeiro)

 


