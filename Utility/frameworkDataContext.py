class CustomContext:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.user_data = {}
            cls._instance.test_data = {}
            cls._instance.step_data = {}
            cls._instance.feature_data = {}  # Data shared across scenarios within the same feature
        return cls._instance

    @staticmethod
    def set_user_data(key, value):
        """Set user data in the context."""
        CustomContext().user_data[key] = value

    @staticmethod
    def get_user_data(key):
        """Get user data from the context."""
        return CustomContext().user_data.get(key)

    @staticmethod
    def reset_user_data(key):
        """Reset the value for a specific key in user data."""
        CustomContext().user_data[key] = None

    def set_test_data(self, key, value):
        """Set test data in the context."""
        self.test_data[key] = value

    def get_test_data(self, key):
        """Get test data from the context."""
        return self.test_data.get(key)

    def reset_step_data(self):
        """Reset step data after each step."""
        self.step_data = {}  # Reset step-specific data

    def set_step_data(self, key, value):
        """Set data for a specific step."""
        self.step_data[key] = value

    def get_step_data(self, key):
        """Get step-specific data."""
        return self.step_data.get(key)

    # New methods for feature-specific data
    def set_feature_data(self, key, value):
        """Set data for a specific feature (shared across scenarios)."""
        self.feature_data[key] = value

    def get_feature_data(self, key):
        """Get feature-specific data."""
        return self.feature_data.get(key)

    def reset_feature_data(self):
        """Reset feature data between features."""
        self.feature_data = {}  # Reset feature-specific data
