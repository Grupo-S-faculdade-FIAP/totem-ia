"""
SUSTAINABILITY PROMPTS
======================
Arquivo de prompts para o agent de sustentabilidade.
Focado em tampinhas recicláveis.
"""

# System Prompt para o agente de sustentabilidade
SYSTEM_PROMPT = """Você é um assistente educativo especializado em sustentabilidade ambiental, 
reciclagem e principalmente na importância das tampinhas recicláveis. 
Seu tom é motivador, positivo e inspirador."""

# Prompt do usuário para geração de script sobre tampinhas recicláveis
USER_PROMPT = """Gere um script de áudio engajante e educativo especificamente sobre 
TAMPINHAS RECICLÁVEIS e sua importância para o meio ambiente.

O script deve:
- Durar entre 30-45 segundos quando lido em voz alta
- Ser motivador, positivo e inspirador
- Focar ESPECIFICAMENTE em tampinhas de plástico e sua reciclagem
- Explicar por que tampinhas recicláveis são importantes
- Destacar o impacto ambiental positivo da reciclagem de tampinhas
- Incluir dados/curiosidades sobre tampinhas e meio ambiente
- Terminar com uma chamada à ação persuasiva
- Ser apropriado para uso em um totem interativo em espaço público
- Usar linguagem simples e acessível

Apenas retorne o texto do script, sem explicações adicionais."""

# Prompt alternativo mais específico
USER_PROMPT_ALT = """Crie um discurso motivador de 35 segundos sobre a reciclagem de tampinhas plásticas.

Requisitos:
✓ Destacar que tampinhas são totalmente recicláveis
✓ Mencionar o tempo de decomposição (400+ anos)
✓ Explicar o ciclo de vida de uma tampinha reciclada
✓ Incluir dados sobre quantidade de tampinhas nos oceanos
✓ Convencer pessoas a reciclar tampinhas agora
✓ Terminar com frase impactante sobre sustentabilidade

Retorne APENAS o texto do script."""

# Prompt para versão infantil
USER_PROMPT_KIDS = """Crie um script divertido e educativo sobre reciclar tampinhas,
para crianças de 6-12 anos.

O script deve:
- Ser curto (20-25 segundos)
- Usar linguagem lúdica e divertida
- Comparar tampinhas com personagens ou super-heróis
- Explicar que tampinhas viram coisas legais quando recicladas
- Fazer as crianças quererem reciclar tampinhas
- Terminar com um desafio divertido

Apenas o texto do script, sem explicações."""

# Prompt para versão técnica/dados
USER_PROMPT_TECHNICAL = """Gere um script técnico e informativo sobre tampinhas recicláveis
com foco em dados e estatísticas.

Incluir:
- Quantas tampinhas são recicladas anualmente no Brasil
- Composição das tampinhas (polipropileno, polietileno)
- Temperatura de fusão e processos de reciclagem
- Produtos finais (fibras, pellets, objetos)
- Economia de recursos (energia, água, CO2)
- Certificações e padrões de reciclagem

Duração: 40-50 segundos
Apenas o texto do script."""

# Exemplos de saídas esperadas
EXAMPLE_OUTPUTS = [
    """Olá! Você sabia que cada tampinha de plástico demora mais de 400 anos para se decompor? 
    Mas aqui está a boa notícia: tampinhas são 100% recicláveis! Quando você recicla uma tampinha, 
    ela se torna uma nova fibra têxtil, um novo brinquedo, ou até um novo objeto útil. 
    Bilhões de tampinhas acabam nos oceanos e aterros todos os anos. 
    Sua ação importa! Recicle suas tampinhas agora e ajude a proteger nosso planeta. 
    Cada tampinha reciclada é uma vitória para a sustentabilidade!""",
    
    """Reciclar tampinhas é um superpoder ambiental! Tampinhas de plástico podem ser transformadas 
    em fibras para roupas, móveis sustentáveis, objetos de design e muito mais. 
    Você sabia que uma única tampinha tem potencial infinito de reuso? 
    O polipropileno das tampinhas é um material nobre para reciclagem. 
    Proteja a vida marinha! Proteja as florestas! Proteja nosso futuro! 
    Deposite suas tampinhas aqui agora e seja um guerreiro da sustentabilidade!""",
    
    """Tampinhas recicláveis: pequenas ações, grande impacto! 
    Cada tampinha que você recicla poupa recursos naturais valiosos. 
    Menos extração de petróleo, menos energia consumida, menos poluição. 
    As tampinhas viram incríveis materiais: fibras têxteis, peças de automóvel, utensílios. 
    Imagine um mundo onde todas as tampinhas fossem recicladas! 
    Comece agora! Sua tampinha é valiosa! Recicle!""",
]

# Tags/keywords para rastreamento
TAGS = [
    "tampinhas",
    "recicláveis",
    "sustentabilidade",
    "reciclagem",
    "plástico",
    "meio-ambiente",
    "educação-ambiental",
    "impacto-positivo",
]

if __name__ == "__main__":
    print("=" * 70)
    print("PROMPTS: Sustainability Agent - Tampinhas Recicláveis")
    print("=" * 70)
    print(f"\nSYSTEM PROMPT:")
    print(f"{SYSTEM_PROMPT}")
    print(f"\n{'=' * 70}")
    print(f"USER PROMPT (Principal):")
    print(f"{USER_PROMPT}")
    print(f"\n{'=' * 70}")
    print(f"Prompts Alternativos Disponíveis:")
    print(f"  • USER_PROMPT_ALT - Versão específica com dados")
    print(f"  • USER_PROMPT_KIDS - Versão infantil")
    print(f"  • USER_PROMPT_TECHNICAL - Versão técnica com estatísticas")
    print(f"\n{'=' * 70}")
    print(f"EXEMPLOS DE SAÍDA:")
    print(f"{'=' * 70}")
    for i, example in enumerate(EXAMPLE_OUTPUTS, 1):
        print(f"\nExemplo {i}:")
        print(f"{example}\n")
