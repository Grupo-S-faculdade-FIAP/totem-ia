#!/usr/bin/env python3
"""
Script de testes para o sistema de recompensas TAMPS
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5003"

def print_header(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_rewards_api():
    """Testa todos os endpoints do sistema de recompensas"""
    
    print_header("🎯 TESTES DO SISTEMA DE RECOMPENSAS TAMPS")
    
    user_id = "test_user_001"
    
    # 1. Obter dados do usuário (novo)
    print("\n1️⃣  Obtendo dados do usuário...")
    response = requests.get(f"{BASE_URL}/api/rewards/user/{user_id}")
    print(f"Status: {response.status_code}")
    user_data = response.json()
    print(f"Resposta: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
    
    # 2. Adicionar primeira tampinha
    print("\n2️⃣  Adicionando primeira tampinha (+10 pontos)...")
    response = requests.post(
        f"{BASE_URL}/api/rewards/add-cap",
        json={"user_id": user_id, "points": 10, "cap_type": "plastic"}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Resposta: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 3. Adicionar mais tampinhas
    print("\n3️⃣  Adicionando 5 tampinhas adicionais...")
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/api/rewards/add-cap",
            json={"user_id": user_id, "points": 10, "cap_type": "plastic"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Tampinha {i+2}: +10 pontos | Total: {data['user_data']['total_points']} TAMPS")
    
    # 4. Obter dados atualizados
    print("\n4️⃣  Obtendo dados atualizados do usuário...")
    response = requests.get(f"{BASE_URL}/api/rewards/user/{user_id}")
    user_data = response.json()
    print(f"👤 ID: {user_data['id']}")
    print(f"⭐ Pontos Totais: {user_data['total_points']} TAMPS")
    print(f"♻️  Tampinhas Depositadas: {user_data['caps_deposited']}")
    
    # 5. Obter lista de parceiros
    print("\n5️⃣  Obtendo lista de parceiros disponíveis...")
    response = requests.get(f"{BASE_URL}/api/rewards/partners")
    print(f"Status: {response.status_code}")
    partners_data = response.json()
    print(f"\n🏢 {partners_data['count']} parceiros disponíveis:\n")
    
    for partner in partners_data['partners']:
        print(f"   {partner['icon']} {partner['name']}")
        print(f"      └─ {partner['description']}")
        print(f"      └─ Pontos necessários: {partner['points_required']} TAMPS\n")
    
    # 6. Tentar resgatar uma recompensa
    print("\n6️⃣  Tentando resgatar recompensa (Starbucks - 100 pontos)...")
    response = requests.post(
        f"{BASE_URL}/api/rewards/redeem",
        json={"user_id": user_id, "partner_id": "starbucks"}
    )
    print(f"Status: {response.status_code}")
    redeem_result = response.json()
    print(f"Resposta: {json.dumps(redeem_result, indent=2, ensure_ascii=False)}")
    
    # 7. Verificar dados após resgate
    print("\n7️⃣  Verificando dados após resgate...")
    response = requests.get(f"{BASE_URL}/api/rewards/user/{user_id}")
    user_data = response.json()
    print(f"⭐ Pontos Restantes: {user_data['total_points']} TAMPS")
    
    # 8. Obter ranking
    print("\n8️⃣  Obtendo ranking de top usuários...")
    response = requests.get(f"{BASE_URL}/api/rewards/leaderboard?limit=5")
    print(f"Status: {response.status_code}")
    leaderboard = response.json()
    print(f"\n🏆 Top {leaderboard['count']} usuários:\n")
    
    for idx, user in enumerate(leaderboard['leaderboard'], 1):
        print(f"   {idx}. {user['id']}")
        print(f"      └─ {user['total_points']} pontos | {user['caps_deposited']} tampinhas\n")
    
    # 9. Adicionar outro usuário para teste de ranking
    print("\n9️⃣  Adicionando segundo usuário para teste de ranking...")
    user2_id = "test_user_002"
    for i in range(15):  # 150 pontos
        requests.post(
            f"{BASE_URL}/api/rewards/add-cap",
            json={"user_id": user2_id, "points": 10, "cap_type": "plastic"}
        )
    print(f"✅ Usuário 2 criado com 150 pontos")
    
    # 10. Ranking atualizado
    print("\n🔟 Ranking final:")
    response = requests.get(f"{BASE_URL}/api/rewards/leaderboard?limit=5")
    leaderboard = response.json()
    
    for idx, user in enumerate(leaderboard['leaderboard'], 1):
        print(f"   {idx}. {user['id']}: {user['total_points']} TAMPS ({user['caps_deposited']} ♻️)")
    
    print_header("✅ TESTES CONCLUÍDOS COM SUCESSO!")

if __name__ == "__main__":
    try:
        test_rewards_api()
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor.")
        print("   Certifique-se de que o Flask está rodando em http://localhost:5003")
    except Exception as e:
        print(f"❌ Erro: {e}")
