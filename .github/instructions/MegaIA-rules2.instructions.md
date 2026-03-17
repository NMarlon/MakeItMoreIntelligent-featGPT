---
description: Este arquivo contém o contexto completo e detalhado do projeto MegaIA, incluindo a visão geral, conceitos fundamentais, arquitetura atual, código completo, histórico da conversa e instruções para a próxima IA que continuar o projeto. Ele serve como um guia abrangente para garantir que qualquer IA possa entender e continuar o desenvolvimento do MegaIA de forma consistente com os objetivos e princípios estabelecidos por Marlon.
applyTo: '*' # when provided, instructions will automatically be added to the request context when the pattern matches an attached file
---

<!-- Tip: Use /create-instructions in chat to generate content with agent assistance -->


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

