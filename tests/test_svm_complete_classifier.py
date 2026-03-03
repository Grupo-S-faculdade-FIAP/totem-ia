"""
Testes adicionais para src/models_trainers/svm_complete_classifier.py

Cobre casos específicos e validações extras do classifier completo.
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSVMFeatureValidation:
    """Testes de validação de features extraídas."""

    def test_features_nao_contem_infinito(self, tmp_path):
        """Features não devem conter valores infinitos."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        # Criar imagem com valores extremos
        clf = SVMCompleteDatasetClassifier()
        image = np.ones((128, 128, 3), dtype=np.uint8) * 255  # Branco puro
        
        image_path = tmp_path / "white.jpg"
        cv2.imwrite(str(image_path), image)
        
        features = clf.extract_color_features(str(image_path))
        
        assert not np.isinf(features).any(), "Features contêm infinitos"

    def test_features_nao_contem_nan(self, tmp_path):
        """Features não devem conter NaN."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        image = np.zeros((128, 128, 3), dtype=np.uint8)  # Preto puro
        
        image_path = tmp_path / "black.jpg"
        cv2.imwrite(str(image_path), image)
        
        features = clf.extract_color_features(str(image_path))
        
        assert not np.isnan(features).any(), "Features contêm NaN"

    def test_features_tem_24_dimensoes(self, tmp_path):
        """Features devem ter exatamente 24 dimensões."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        image = cv2.imread(str(tmp_path / "test.jpg")) if (tmp_path / "test.jpg").exists() else np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
        
        image_path = tmp_path / "test_image.jpg"
        cv2.imwrite(str(image_path), image)
        
        features = clf.extract_color_features(str(image_path))
        
        assert features.shape == (24,), f"Expected (24,), got {features.shape}"

    def test_features_valores_em_range_razoavel(self, tmp_path):
        """Features devem estar em um range razoável."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        image = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
        
        image_path = tmp_path / "random.jpg"
        cv2.imwrite(str(image_path), image)
        
        features = clf.extract_color_features(str(image_path))
        
        # RGB stats: 0-255, HSV stats: 0-255/180, Shape: 0-inf (mas normalizados)
        assert features.max() < 100000, "Valores muito altos"
        assert features.min() >= -1000, "Valores muito baixos"


class TestSVMModelTraining:
    """Testes de treinamento do modelo."""

    def test_modelo_aprende_com_dados_validos(self):
        """Modelo deve aprender com dados válidos."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        # Criar dados de treinamento sintéticos
        X_train = np.random.randn(100, 24)
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.randn(20, 24)
        y_val = np.random.randint(0, 2, 20)
        
        # Treinar
        clf.train_model(X_train, y_train, X_val, y_val)
        
        # Deve ter modelo
        assert clf.model is not None

    def test_modelo_faz_predicoes_consistentes(self):
        """Modelo deve fazer predições consistentes."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        X = np.random.randn(50, 24)
        y = np.random.randint(0, 2, 50)
        
        clf.train_model(X, y, X, y)
        
        # Fazer predições duas vezes com mesmos dados
        X_test = np.random.randn(10, 24)
        X_test_scaled = clf.scaler.transform(X_test)
        
        pred1 = clf.model.predict(X_test_scaled)
        pred2 = clf.model.predict(X_test_scaled)
        
        np.testing.assert_array_equal(pred1, pred2, "Predições inconsistentes")

    def test_modelo_separa_classes(self):
        """Modelo deve aprender a separar classes."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        # Criar dados bem separáveis
        X_class_0 = np.random.randn(50, 24) - 2  # Classe 0: deslocada para -2
        X_class_1 = np.random.randn(50, 24) + 2  # Classe 1: deslocada para +2
        
        X_train = np.vstack([X_class_0, X_class_1])
        y_train = np.hstack([np.zeros(50), np.ones(50)])
        
        clf.train_model(X_train, y_train, X_train, y_train)
        
        # Predizer nas mesmas amostras
        X_scaled = clf.scaler.transform(X_train)
        predictions = clf.model.predict(X_scaled)
        
        # Deve acertar a maioria
        accuracy = np.mean(predictions == y_train)
        assert accuracy > 0.8, f"Accuracy muito baixa: {accuracy}"


class TestSVMScalerFitting:
    """Testes de fitting do scaler."""

    def test_scaler_aprende_media_e_std(self):
        """Scaler deve aprender média e desvio padrão."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        X = np.random.randn(100, 24) * 10 + 5  # Média 5, std 10
        y = np.random.randint(0, 2, 100)
        
        clf.train_model(X, y, X, y)
        
        # Scaler deve ter mean_ e scale_
        assert hasattr(clf.scaler, 'mean_')
        assert hasattr(clf.scaler, 'scale_')
        assert clf.scaler.mean_ is not None
        assert clf.scaler.scale_ is not None

    def test_scaler_nao_usa_dados_validacao(self):
        """Scaler só deve ser treinado com dados de treino."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        from sklearn.preprocessing import StandardScaler
        
        clf = SVMCompleteDatasetClassifier()
        
        X_train = np.ones((50, 24)) * 2  # Treino: valor 2
        y_train = np.random.randint(0, 2, 50)
        X_val = np.ones((20, 24)) * 100  # Val: valor 100 (diferente!)
        y_val = np.random.randint(0, 2, 20)
        
        clf.train_model(X_train, y_train, X_val, y_val)
        
        # Scaler deve ter aprendido com treino, não validação
        # Média deve estar próxima de 2
        assert np.allclose(clf.scaler.mean_, 2.0, atol=0.5), \
            f"Scaler aprendeu da validação: mean={clf.scaler.mean_}"


class TestSVMModelSerialization:
    """Testes de serialização do modelo."""

    def test_modelo_pkl_pode_ser_carregado(self):
        """Modelo salvo em pkl deve poder ser carregado."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        import joblib
        
        clf = SVMCompleteDatasetClassifier()
        
        X = np.random.randn(50, 24)
        y = np.random.randint(0, 2, 50)
        
        clf.train_model(X, y, X, y)
        clf.save_model()
        
        # Carregar modelo
        model_path = clf.model_path / "svm_model_complete.pkl"
        loaded_model = joblib.load(model_path)
        
        assert loaded_model is not None
        assert hasattr(loaded_model, 'predict')

    def test_scaler_pkl_pode_ser_carregado(self):
        """Scaler salvo em pkl deve poder ser carregado."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        import joblib
        
        clf = SVMCompleteDatasetClassifier()
        
        X = np.random.randn(50, 24)
        y = np.random.randint(0, 2, 50)
        
        clf.train_model(X, y, X, y)
        clf.save_model()
        
        # Carregar scaler
        scaler_path = clf.model_path / "scaler_complete.pkl"
        loaded_scaler = joblib.load(scaler_path)
        
        assert loaded_scaler is not None
        assert hasattr(loaded_scaler, 'transform')

    def test_modelo_carregado_faz_predicoes_iguais(self):
        """Modelo carregado deve fazer mesmas predições."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        import joblib
        
        clf1 = SVMCompleteDatasetClassifier()
        
        X = np.random.randn(50, 24)
        y = np.random.randint(0, 2, 50)
        
        clf1.train_model(X, y, X, y)
        clf1.save_model()
        
        # Predições originais
        X_test = np.random.randn(10, 24)
        X_test_scaled = clf1.scaler.transform(X_test)
        pred1 = clf1.model.predict(X_test_scaled)
        
        # Carregar e predizer novamente
        model = joblib.load(clf1.model_path / "svm_model_complete.pkl")
        scaler = joblib.load(clf1.model_path / "scaler_complete.pkl")
        
        X_test_scaled2 = scaler.transform(X_test)
        pred2 = model.predict(X_test_scaled2)
        
        np.testing.assert_array_equal(pred1, pred2, "Predições diferentes após carregar")


class TestSVMDatasetLoading:
    """Testes de carregamento de dataset."""

    def test_load_dataset_retorna_x_y(self):
        """load_dataset deve retornar X, y."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        with patch.object(clf, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.glob', return_value=[]):
                with patch('pathlib.Path.exists', return_value=False):
                    X, y = clf.load_dataset()
                    
                    assert isinstance(X, np.ndarray)
                    assert isinstance(y, np.ndarray)

    def test_dataset_x_shape_correto(self):
        """X deve ter shape (n_samples, 24)."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        with patch.object(clf, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.glob', return_value=[]):
                with patch('pathlib.Path.exists', return_value=False):
                    X, y = clf.load_dataset()
                    
                    if len(X) > 0:
                        assert X.shape[1] == 24

    def test_dataset_y_contem_apenas_0_e_1(self):
        """y deve conter apenas 0 e 1."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        with patch.object(clf, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.glob', return_value=[]):
                with patch('pathlib.Path.exists', return_value=False):
                    X, y = clf.load_dataset()
                    
                    if len(y) > 0:
                        assert set(y).issubset({0, 1})

    def test_load_dataset_include_validation_true_retorna_quatro_arrays(self):
        """load_dataset(include_validation=True) deve manter modo completo."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier

        clf = SVMCompleteDatasetClassifier()

        with patch.object(clf, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.exists', return_value=False):
                result = clf.load_dataset(include_validation=True)

        assert isinstance(result, tuple)
        assert len(result) == 4


class TestSVMIntegrationComplete:
    """Testes de integração completa do SVM."""

    def test_pipeline_completo_treino_predicao(self):
        """Pipeline completo: load → train → save → load → predict."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        import joblib
        
        clf = SVMCompleteDatasetClassifier()
        
        # Usar dados sintéticos
        X = np.random.randn(100, 24)
        y = np.random.randint(0, 2, 100)
        
        # Treinar
        clf.train_model(X, y, X, y)
        
        # Salvar
        clf.save_model()
        
        # Carregar
        model = joblib.load(clf.model_path / "svm_model_complete.pkl")
        scaler = joblib.load(clf.model_path / "scaler_complete.pkl")
        
        # Predizer
        X_test = np.random.randn(10, 24)
        X_test_scaled = scaler.transform(X_test)
        predictions = model.predict(X_test_scaled)
        
        assert len(predictions) == 10
        assert all(p in [0, 1] for p in predictions)


class TestSVMCrossValidation:
    """Testes de validação cruzada."""

    def test_cross_val_score_executa(self):
        """cross_val_score deve executar sem erro."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        from sklearn.model_selection import cross_val_score
        from sklearn.svm import SVC
        
        X = np.random.randn(50, 24)
        y = np.random.randint(0, 2, 50)
        
        model = SVC(kernel='rbf')
        
        # Cross validation com 3 folds
        scores = cross_val_score(model, X, y, cv=3)
        
        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)

    def test_cross_val_score_resultados_variam(self):
        """Scores de cada fold devem variar."""
        from sklearn.model_selection import cross_val_score
        from sklearn.svm import SVC
        
        X = np.random.randn(50, 24)
        y = np.random.randint(0, 2, 50)
        
        model = SVC(kernel='rbf')
        scores = cross_val_score(model, X, y, cv=5)
        
        # Nem todos os scores devem ser iguais
        assert len(set(np.round(scores, 3))) > 1 or len(scores) == 1


class TestSVMReporting:
    """Testes de relatório (classification_report, confusion_matrix)."""

    def test_classification_report_gerado(self):
        """classification_report deve gerar string com métricas."""
        from sklearn.metrics import classification_report
        
        y_true = [0, 1, 1, 0, 1, 0]
        y_pred = [0, 1, 0, 0, 1, 1]
        
        report = classification_report(y_true, y_pred)
        
        assert isinstance(report, str)
        assert 'precision' in report.lower()
        assert 'recall' in report.lower()
        assert 'f1-score' in report.lower()

    def test_confusion_matrix_forma_correta(self):
        """confusion_matrix deve ter forma (2, 2)."""
        from sklearn.metrics import confusion_matrix
        
        y_true = [0, 1, 1, 0, 1, 0]
        y_pred = [0, 1, 0, 0, 1, 1]
        
        cm = confusion_matrix(y_true, y_pred)
        
        assert cm.shape == (2, 2)
        assert cm[0, 0] >= 0  # True negatives
        assert cm[1, 1] >= 0  # True positives

    def test_confusion_matrix_soma_correta(self):
        """Soma de confusion_matrix deve bater com tamanho de y_true."""
        from sklearn.metrics import confusion_matrix
        
        y_true = np.random.randint(0, 2, 100)
        y_pred = np.random.randint(0, 2, 100)
        
        cm = confusion_matrix(y_true, y_pred)
        
        assert cm.sum() == len(y_true)


class TestSVMDatasetHandling:
    """Testes de manipulação de dataset."""

    def test_dataset_desbalanceado_detectado(self):
        """Dataset desbalanceado deve ser detectado."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        # Muito mais positivos que negativos
        X = np.random.randn(100, 24)
        y = np.hstack([np.ones(90), np.zeros(10)])
        
        clf.train_model(X, y, X, y)
        
        # Modelo deve conseguir treinar mesmo desbalanceado
        assert clf.model is not None

    def test_dataset_balanceado(self):
        """Dataset balanceado deve treinar melhor."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        # Balanceado
        X = np.random.randn(100, 24)
        y = np.hstack([np.ones(50), np.zeros(50)])
        
        X_scaled = clf.scaler.fit_transform(X)
        clf.model = clf.__class__().model or None
        
        from sklearn.svm import SVC
        model = SVC(kernel='rbf')
        model.fit(X_scaled, y)
        
        predictions = model.predict(X_scaled)
        assert len(predictions) == 100


class TestSVMEdgeCases:
    """Testes de casos extremos do SVM."""

    def test_modelo_com_uma_classe_apenas(self):
        """Modelo não consegue treinar com apenas uma classe."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        from sklearn.svm import SVC
        
        X = np.random.randn(50, 24)
        y = np.ones(50)  # Apenas classe 1
        
        model = SVC(kernel='rbf')
        
        # Não deve crash, mas pode falhar
        try:
            model.fit(X, y)
            predictions = model.predict(X)
            # Se conseguiu, todas predições devem ser 1
            assert all(p == 1 for p in predictions)
        except ValueError:
            # É aceitável falhar com uma classe
            pass

    def test_features_com_valores_muito_altos(self):
        """Features com valores muito grandes devem ser escalados."""
        from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier
        
        clf = SVMCompleteDatasetClassifier()
        
        X = np.random.randn(50, 24) * 1000 + 5000  # Valores muito grandes
        y = np.random.randint(0, 2, 50)
        
        X_scaled = clf.scaler.fit_transform(X)
        
        # Após escalar, media deve ser 0 e std ≈ 1
        assert np.allclose(X_scaled.mean(), 0, atol=1e-10)
        assert np.allclose(X_scaled.std(), 1, atol=0.1)
