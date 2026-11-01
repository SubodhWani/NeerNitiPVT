class MLEngine:
    def __init__(self):
        self._is_ready = False
        self.model_loaded = False
        self.gee_authenticated = False
        self.num_reference_wells = 1690
        self.decision_thresholds = {"tier_1": 0.45, "tier_2": 0.37}

    def initialize(self):
        """Loads GEE credentials, ML model, etc."""
        # Add actual loading logic here
        self.model_loaded = True
        self.gee_authenticated = True
        self._is_ready = True

    def shutdown(self):
        """Cleans up ML Engine resources"""
        self.model_loaded = False
        self.gee_authenticated = False
        self._is_ready = False

    @property
    def is_ready(self):
        return self._is_ready

ml_engine = MLEngine()
