from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    # GA Parameters (defaults)
    POPULATION_SIZE: int = 100
    NUM_GENERATIONS: int = 200
    TOURNAMENT_SIZE: int = 5
    CROSSOVER_RATE: float = 0.8
    MUTATION_RATE: float = 0.15
    ELITISM_COUNT: int = 3

    EARLY_STOPPING_ENABLED: bool = True
    EARLY_STOPPING_PATIENCE: int = 50
    EARLY_STOPPING_MIN_DELTA: float = 0.00005

    WEIGHT_DISTANCE: float = 0.8
    WEIGHT_UNUSED_CAPACITY: float = 0.2

    EMISSION_FACTOR: float = 0.0000191

    TRUCK_CAPACITY: int = 150
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()