from cnfgen import RandomKCNF
import random
import tqdm 

K = 3 
SEED = 100 
LEN = 50_000 
FOLDER = "formulas"

print(f"Creating {LEN} samples in {FOLDER}") 

random.seed(SEED) 

seed = SEED 
for i in tqdm.tqdm(range(LEN)):
    n = random.randint(200, 300) 
    m = int(4.258 * n + 58.26 * pow(n, -2 / 3.)) 
    cnf = RandomKCNF(K, n, m, seed=seed).to_file(f"{FOLDER}/{i}.cnf", export_header=False) 
    seed += 1 
