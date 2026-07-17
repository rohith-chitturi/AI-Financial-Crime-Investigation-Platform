from faker import Faker
import random

# Use a fixed seed for reproducibility across environments
SEED = 42

def get_faker() -> Faker:
    fake = Faker()
    fake.seed_instance(SEED)
    random.seed(SEED)
    return fake
