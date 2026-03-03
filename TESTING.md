# 🧪 Guia de Testes — TOTEM IA

## Estrutura

```
tests/
├── __init__.py
├── conftest.py              # Fixtures reutilizáveis
├── test_classify.py         # Testes do ImageClassifier
├── test_database.py         # Testes do DatabaseConnection
├── test_routes.py           # Testes das rotas Flask
├── test_debug_mode.py       # Testes do modo debug
├── test_esp32_integration.py  # Testes de integração ESP32
└── test_esp32_server.py     # Testes do servidor ESP32

conftest.py                 # Fixtures globais
pytest.ini                  # Configuração do pytest
.coveragerc                 # Configuração de cobertura
```

## Executar Testes

### Ativar ambiente virtual
```bash
source venv/bin/activate
```

### Todos os testes
```bash
pytest
```

### Testes específicos
```bash
# Apenas testes unitários
pytest tests/test_classify.py tests/test_database.py

# Apenas testes de integração
pytest tests/test_routes.py tests/test_esp32_integration.py

# Teste específico
pytest tests/test_classify.py::TestClassifyImage::test_sat_high
```

### Com cobertura de código
```bash
# Gerar relatório de cobertura
pytest --cov=src --cov=app --cov-report=html --cov-report=term-missing

# Abrir relatório HTML
open htmlcov/index.html
```

### Verbose e debug
```bash
# Modo verbose
pytest -v

# Com logs de debug
pytest -vv --tb=long

# Mostrar print statements
pytest -s
```

### Por marcadores
```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Excluir testes lentos
pytest -m "not slow"
```

## Padrão AAA (Arrange-Act-Assert)

Todos os testes seguem este padrão:

```python
def test_classify_image_returns_tampinha_for_high_saturation():
    # Arrange — setup das dependências e dados
    classifier = ImageClassifier()
    classifier.model = mock_model
    image = create_image_with_saturation(150)

    # Act — executar a ação
    pred, conf, sat, method = classifier.classify_image(image)

    # Assert — verificar resultados
    assert pred == 1
    assert conf >= 0.90
    assert method == "SAT_HIGH"
```

## Mocking de Dependências

### Mockar classificador
```python
@pytest.fixture
def mock_classifier():
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    return classifier
```

### Mockar banco de dados
```python
@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test_totem.db")
    db = DatabaseConnection(db_path)
    db.init_db()
    return db
```

### Mockar ESP32
```python
@patch('requests.get')
def test_esp32_offline(mock_get):
    mock_get.side_effect = ConnectionError()
    # ... test fallback behavior
```

## Cobertura Esperada

Cada módulo deve ter cobertura **≥ 80%**:

- ✅ `src/modules/image.py` — todos os caminhos de classificação
- ✅ `src/database/db.py` — CRUD e queries
- ✅ `app.py` — rotas /api/health, /api/classify, validação
- ✅ `src/hardware/esp32.py` — conexão e timeout

### Excluído de cobertura
- Código de terceiros (Flask, OpenCV, sklearn)
- Getters/setters triviais
- Constantes e enums

## Ci/Cd

### Pré-commit hooks (futuro)
```bash
# Rodar testes antes de commit
pre-commit run pytest
```

### GitHub Actions (futuro)
```yaml
- name: Run tests with coverage
  run: pytest --cov=src --cov=app --cov-report=xml
```
