#!/usr/bin/env python3
"""
EXEMPLOS PRÁTICOS - Como usar o sistema de recompensas TAMPS
"""

import requests
import json

BASE_URL = "http://localhost:5003"

# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO 1: Novo usuário deposita 10 tampinhas
# ═══════════════════════════════════════════════════════════════════════════════

def exemplo_1_novo_usuario():
    print("\n📱 EXEMPLO 1: Novo Usuário deposita 10 tampinhas\n")
    
    user_id = "carolinator_001"
    
    # Adicionar 10 tampinhas
    for i in range(10):
        response = requests.post(
            f"{BASE_URL}/api/rewards/add-cap",
            json={
                "user_id": user_id,
                "points": 10,
                "cap_type": "plastic"
            }
        )
        
        if response.ok:
            data = response.json()
            print(f"   Tampinha {i+1}: +10 pontos | Saldo: {data['user_data']['total_points']} TAMPS")
    
    # Verificar dados finais
    response = requests.get(f"{BASE_URL}/api/rewards/user/{user_id}")
    user = response.json()
    
    print(f"\n✅ Total acumulado: {user['total_points']} TAMPS")
    print(f"   Membro desde: {user['created_at']}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO 2: Consultar parceiros e resgatar
# ═══════════════════════════════════════════════════════════════════════════════

def exemplo_2_resgatar_recompensa():
    print("\n🏆 EXEMPLO 2: Consultar parceiros e resgatar\n")
    
    user_id = "carolinator_001"
    
    # Listar parceiros
    response = requests.get(f"{BASE_URL}/api/rewards/partners")
    partners = response.json()['partners']
    
    print("Parceiros disponíveis:\n")
    for idx, p in enumerate(partners, 1):
        print(f"{idx}. {p['icon']} {p['name']:15} - {p['points_required']} TAMPS")
    
    # Tentar resgatar Starbucks (100 TAMPS)
    print(f"\n🎯 Tentando resgatar: Starbucks (100 TAMPS)...\n")
    
    response = requests.post(
        f"{BASE_URL}/api/rewards/redeem",
        json={
            "user_id": user_id,
            "partner_id": "starbucks"
        }
    )
    
    if response.ok:
        result = response.json()
        print(f"✅ Resgate confirmado!")
        print(f"   Recompensa: {result['reward']}")
        print(f"   Pontos restantes: {result['remaining_points']} TAMPS\n")
    else:
        error = response.json()
        print(f"❌ {error['error']}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO 3: Ver ranking com múltiplos usuários
# ═══════════════════════════════════════════════════════════════════════════════

def exemplo_3_ranking():
    print("\n🏆 EXEMPLO 3: Ranking de Usuários\n")
    
    # Criar 3 usuários com diferentes pontos
    users_data = [
        {"id": "alice", "points": 250},
        {"id": "bob", "points": 180},
        {"id": "carol", "points": 150},
    ]
    
    # Adicionar pontos aos usuários
    for user_info in users_data:
        num_caps = user_info["points"] // 10
        for _ in range(num_caps):
            requests.post(
                f"{BASE_URL}/api/rewards/add-cap",
                json={
                    "user_id": user_info["id"],
                    "points": 10,
                    "cap_type": "plastic"
                }
            )
    
    # Buscar ranking
    response = requests.get(f"{BASE_URL}/api/rewards/leaderboard?limit=5")
    leaderboard = response.json()['leaderboard']
    
    print("🥇 TOP USUÁRIOS:\n")
    for idx, user in enumerate(leaderboard, 1):
        medal = ["🥇", "🥈", "🥉"][idx-1] if idx <= 3 else f"{idx}."
        print(f"{medal} {user['id']:15} | {user['total_points']:3} TAMPS | {user['caps_deposited']} ♻️")
    
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO 4: Histórico de transações
# ═══════════════════════════════════════════════════════════════════════════════

def exemplo_4_historico():
    print("\n📋 EXEMPLO 4: Histórico de Transações\n")
    
    user_id = "alice"
    
    # Adicionar tampinhas
    print(f"Adicionando 5 tampinhas para {user_id}...\n")
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/api/rewards/add-cap",
            json={
                "user_id": user_id,
                "points": 10,
                "cap_type": "plastic"
            }
        )
    
    # Consultar dados
    response = requests.get(f"{BASE_URL}/api/rewards/user/{user_id}")
    user = response.json()
    
    print(f"Dados do usuário {user_id}:")
    print(f"  ⭐ Pontos totais: {user['total_points']} TAMPS")
    print(f"  ♻️  Tampinhas: {user['caps_deposited']}")
    print(f"  📅 Membro desde: {user['created_at']}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO 5: Caso de uso completo (simulação)
# ═══════════════════════════════════════════════════════════════════════════════

def exemplo_5_caso_completo():
    print("\n🎮 EXEMPLO 5: Caso de Uso Completo\n")
    
    print("=" * 70)
    print("SIMULAÇÃO: João deposita tampinhas e resgata cupom")
    print("=" * 70)
    
    user_id = "joao_silva"
    
    # Passo 1: Depositar tampinhas
    print(f"\n📱 Passo 1: {user_id} começa a depositar tampinhas no TOTEM")
    print("-" * 70)
    
    tampinhas_total = 15
    for i in range(tampinhas_total):
        response = requests.post(
            f"{BASE_URL}/api/rewards/add-cap",
            json={"user_id": user_id, "points": 10}
        )
        if (i + 1) % 5 == 0:
            data = response.json()
            print(f"  ✓ {i+1} tampinhas depositadas → {data['user_data']['total_points']} TAMPS acumulados")
    
    # Passo 2: Consultar saldo
    print(f"\n💰 Passo 2: Verificar saldo de pontos")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/rewards/user/{user_id}")
    user = response.json()
    print(f"  Saldo atual: {user['total_points']} TAMPS")
    
    # Passo 3: Ver opções de resgate
    print(f"\n🎁 Passo 3: Ver parceiros e opções de resgate")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/rewards/partners")
    partners = response.json()['partners']
    
    affordable = [p for p in partners if p['points_required'] <= user['total_points']]
    print(f"  Recompensas que {user_id} pode resgatar:\n")
    
    for p in affordable:
        print(f"    ✓ {p['icon']} {p['name']:15} ({p['points_required']} TAMPS)")
    
    # Passo 4: Resgatar
    print(f"\n🏅 Passo 4: Resgatar Starbucks - Café grátis (100 TAMPS)")
    print("-" * 70)
    
    response = requests.post(
        f"{BASE_URL}/api/rewards/redeem",
        json={"user_id": user_id, "partner_id": "starbucks"}
    )
    
    if response.ok:
        result = response.json()
        print(f"  ✅ Resgate confirmado!")
        print(f"     Cupom: {result['reward']}")
        print(f"     Pontos restantes: {result['remaining_points']} TAMPS")
    
    # Passo 5: Posição no ranking
    print(f"\n🏆 Passo 5: Posição no ranking")
    print("-" * 70)
    
    response = requests.get(f"{BASE_URL}/api/rewards/leaderboard?limit=10")
    leaderboard = response.json()['leaderboard']
    
    position = next((i for i, u in enumerate(leaderboard, 1) if u['id'] == user_id), None)
    if position:
        user_rank = leaderboard[position - 1]
        print(f"  Posição: #{position}")
        print(f"  Pontos: {user_rank['total_points']} TAMPS")
        print(f"  Tampinhas: {user_rank['caps_deposited']}")
    
    print("\n" + "=" * 70)
    print("FIM DA SIMULAÇÃO")
    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("🎮 EXEMPLOS PRÁTICOS - SISTEMA DE RECOMPENSAS TAMPS")
    print("=" * 70)
    print("\nEscolha um exemplo para executar:")
    print("  1. Novo usuário deposita 10 tampinhas")
    print("  2. Consultar parceiros e resgatar")
    print("  3. Ver ranking com múltiplos usuários")
    print("  4. Histórico de transações")
    print("  5. Caso de uso completo (simulação)")
    print("  0. Executar todos os exemplos")
    print()
    
    choice = input("Digite uma opção (0-5): ").strip()
    
    try:
        if choice == "1":
            exemplo_1_novo_usuario()
        elif choice == "2":
            exemplo_2_resgatar_recompensa()
        elif choice == "3":
            exemplo_3_ranking()
        elif choice == "4":
            exemplo_4_historico()
        elif choice == "5":
            exemplo_5_caso_completo()
        elif choice == "0":
            exemplo_1_novo_usuario()
            exemplo_3_ranking()
            exemplo_5_caso_completo()
        else:
            print("❌ Opção inválida!")
    
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor em http://localhost:5003")
        print("   Certifique-se de que Flask está rodando!")
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()
