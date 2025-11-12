from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    # GA Parameters (defaults)
    POPULATION_SIZE: int = 100
    NUM_GENERATIONS: int = 200
    TOURNAMENT_SIZE: int = 5
    CROSSOVER_RATE: float = 0.9
    MUTATION_RATE: float = 0.1
    ELITISM_COUNT: int = 3

    EARLY_STOPPING_ENABLED: bool = True
    EARLY_STOPPING_PATIENCE: int = 20
    EARLY_STOPPING_MIN_DELTA: float = 0.001

    WEIGHT_DISTANCE: float = 1.0
    WEIGHT_UNUSED_CAPACITY: float = 1.0

    EMISSION_FACTOR: float = 0.27  # example kg CO2 per km

    TRUCK_CAPACITY: int = 120
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()