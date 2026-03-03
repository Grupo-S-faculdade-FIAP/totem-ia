"""
Testes do DatabaseConnection — operações de persistência SQLite.

Cobre:
    init_db, save_deposit_data, save_interaction,
    get_total_interacoes, get_all_deposits
"""
import pytest

from src.database.db import DatabaseConnection


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def test_db(tmp_path) -> DatabaseConnection:
    """Banco de dados temporário isolado por teste."""
    db_path = str(tmp_path / "test_totem.db")
    db = DatabaseConnection(db_path)
    db.init_db()
    return db


# =============================================================================
# TestInitDb
# =============================================================================

class TestInitDb:
    def test_cria_tabela_deposits(self, test_db: DatabaseConnection):
        """init_db deve criar a tabela deposits."""
        with test_db as db:
            c = db.conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deposits'")
            assert c.fetchone() is not None

    def test_cria_tabela_interactions(self, test_db: DatabaseConnection):
        """init_db deve criar a tabela interactions."""
        with test_db as db:
            c = db.conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'")
            assert c.fetchone() is not None

    def test_init_db_idempotente(self, test_db: DatabaseConnection):
        """Chamar init_db múltiplas vezes não deve causar erro (IF NOT EXISTS)."""
        test_db.init_db()
        test_db.init_db()


# =============================================================================
# TestSaveDepositData
# =============================================================================

class TestSaveDepositData:
    def test_retorna_id_inteiro(self, test_db: DatabaseConnection):
        """save_deposit_data deve retornar o ID (int) do registro criado."""
        with test_db as db:
            deposit_id = db.save_deposit_data(0.95, True, True, 2500, 0.5)
        assert deposit_id is not None
        assert isinstance(deposit_id, int)
        assert deposit_id > 0

    def test_ids_incrementais(self, test_db: DatabaseConnection):
        """IDs de depósitos consecutivos devem ser crescentes."""
        with test_db as db:
            id1 = db.save_deposit_data(0.90, True, True, 2500, 0.5)
            id2 = db.save_deposit_data(0.85, False, False, 1000, 0.0)
        assert id1 is not None and id2 is not None
        assert id2 > id1

    def test_dados_persistidos_corretamente(self, test_db: DatabaseConnection):
        """Valores inseridos devem ser recuperáveis com os mesmos dados."""
        with test_db as db:
            db.save_deposit_data(0.92, True, True, 2600, 0.5)
            deposits = db.get_all_deposits()
        assert len(deposits) == 1
        dep = deposits[0]
        assert dep['ml_confidence'] == pytest.approx(0.92)
        assert dep['weight_value'] == 2600
        assert dep['plastico_reciclado_g'] == pytest.approx(0.5)

    def test_multiplos_depositos(self, test_db: DatabaseConnection):
        """Deve suportar múltiplos depósitos sem conflito."""
        with test_db as db:
            for i in range(5):
                db.save_deposit_data(0.80 + i * 0.01, True, True, 2500 + i, 0.5)
            deposits = db.get_all_deposits()
        assert len(deposits) == 5


# =============================================================================
# TestSaveInteraction
# =============================================================================

class TestSaveInteraction:
    def test_sucesso_nao_levanta_excecao(self, test_db: DatabaseConnection):
        """save_interaction com SUCESSO não deve levantar exceção."""
        with test_db as db:
            db.save_interaction(DatabaseConnection.ResultadoInteracao.SUCESSO)

    def test_todos_os_resultados_sao_persistidos(self, test_db: DatabaseConnection):
        """Todos os valores do Enum ResultadoInteracao devem ser persistidos."""
        with test_db as db:
            for resultado in DatabaseConnection.ResultadoInteracao:
                db.save_interaction(resultado)

    def test_com_deposit_id_valido(self, test_db: DatabaseConnection):
        """save_interaction com deposit_id deve registrar referência corretamente."""
        with test_db as db:
            deposit_id = db.save_deposit_data(0.95, True, True, 2500, 0.5)
            db.save_interaction(DatabaseConnection.ResultadoInteracao.SUCESSO, deposit_id)

    def test_sem_deposit_id_aceita_none(self, test_db: DatabaseConnection):
        """deposit_id=None (padrão) deve ser aceito sem erro."""
        with test_db as db:
            db.save_interaction(DatabaseConnection.ResultadoInteracao.REJEITADO, None)


# =============================================================================
# TestGetTotalInteracoes
# =============================================================================

class TestGetTotalInteracoes:
    def test_banco_vazio_retorna_zero(self, test_db: DatabaseConnection):
        """Banco sem interações deve retornar 0."""
        with test_db as db:
            total = db.get_total_interacoes()
        assert total == 0

    def test_conta_corretamente(self, test_db: DatabaseConnection):
        """Deve refletir exatamente o número de interações inseridas."""
        with test_db as db:
            db.save_interaction(DatabaseConnection.ResultadoInteracao.SUCESSO)
            db.save_interaction(DatabaseConnection.ResultadoInteracao.REJEITADO)
            db.save_interaction(DatabaseConnection.ResultadoInteracao.ERRO_MECANICA)
            total = db.get_total_interacoes()
        assert total == 3

    def test_retorna_int(self, test_db: DatabaseConnection):
        """O retorno deve ser sempre int."""
        with test_db as db:
            total = db.get_total_interacoes()
        assert isinstance(total, int)


# =============================================================================
# TestGetAllDeposits
# =============================================================================

class TestGetAllDeposits:
    def test_banco_vazio_retorna_lista_vazia(self, test_db: DatabaseConnection):
        """get_all_deposits em banco vazio deve retornar lista vazia."""
        with test_db as db:
            deposits = db.get_all_deposits()
        assert deposits == []

    def test_retorna_lista_de_dicts(self, test_db: DatabaseConnection):
        """Resultado deve ser lista de dicionários."""
        with test_db as db:
            db.save_deposit_data(0.90, True, True, 2500, 0.5)
            deposits = db.get_all_deposits()
        assert isinstance(deposits, list)
        assert isinstance(deposits[0], dict)

    def test_campos_obrigatorios_presentes(self, test_db: DatabaseConnection):
        """Cada depósito deve conter os campos esperados."""
        campos_esperados = {
            'id', 'timestamp', 'ml_confidence',
            'presence_detected', 'weight_value',
            'weight_ok', 'plastico_reciclado_g'
        }
        with test_db as db:
            db.save_deposit_data(0.90, True, True, 2500, 0.5)
            deposits = db.get_all_deposits()
        assert campos_esperados.issubset(set(deposits[0].keys()))
