import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    class RandomForestClassifier:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def fit(self, X, y):
            pass
        def predict(self, X):
            return [0]

class IntentClassifier:
    def __init__(self):
        # Modelo simulado com sklearn (com fallback para CI sem scikit-learn)
        self.clf = RandomForestClassifier(n_estimators=10)
        X_dummy = np.random.rand(10, 5)
        y_dummy = np.random.randint(0, 2, 10)
        self.clf.fit(X_dummy, y_dummy)
        
    def predict_intent(self, state_features: np.ndarray) -> int:
        if len(state_features) != 5:
            state_features = np.zeros(5)
        res = self.clf.predict([state_features])
        return int(res[0]) if isinstance(res, (list, np.ndarray)) else 0

