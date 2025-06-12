from utils.settings import Settings

settings_file = Settings()


def get_trusted_users() -> list[str]:
    return settings_file.get_value("trusted_users")
