"""
SUSTAINABILITY PROMPTS - TAMPINHAS RECICLÁVEIS
==============================================
Prompt FIXO para geração de áudio sobre reciclagem de tampinhas.
Mantido simples e consistente para gerar sempre o mesmo tipo de conteúdo.
"""

# System Prompt para o agente de sustentabilidade
SYSTEM_PROMPT = """Você retorna EXATAMENTE o texto fornecido, sem modificações."""

# SCRIPT FIXO - EXATAMENTE isto que será falado no áudio
SCRIPT_TEXTO = """Olá!    Bem-vindo ao TÓTEM   IÁ. Você sabia que uma tampinha de plástico leva mais de 400 anos para se decompor? 

Mas tampinhas são 100% recicláveis! 
Quando você deposita aqui, ela se torna fibras para roupas, peças de automóvel e muito mais! 

Cada tampinha reciclada, protege a vida marinha e reduz emissões de carbono.    
Sua ação importa!   

Obrigado por reciclar!!"""

# Prompt ÚNICO e FIXO - retorna o script diretamente
USER_PROMPT = SCRIPT_TEXTO


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
    print("PROMPT ÚNICO: Sustainability - Tampinhas Recicláveis")
    print("=" * 70)
    print(f"\nSYSTEM PROMPT:")
    print(f"{SYSTEM_PROMPT}")
    print(f"\n{'=' * 70}")
    print(f"USER PROMPT (FIXO):")
    print(f"{USER_PROMPT}")
    print(f"\n{'=' * 70}")
    print(f"STATUS: ✅ Prompt único e consistente para gerar áudio")

