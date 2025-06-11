from pebble import ProcessPool
from concurrent.futures import TimeoutError
from multiprocessing import Manager
import os 
import glob 
import tqdm 
import pandas as pd
from pysat.formula import CNF
from pysat.solvers import Solver

OUTPUT_FILE = "cnf.csv"
SOLVE_TIMEOUT = True

def process_cnf(results, file_path):
    """
    Process a single formula and return the result.
    """

    cnf = CNF(from_file=file_path) 
    # Create a SAT solver for this formula:
    with Solver(bootstrap_with=cnf, name="Cadical195", use_timer=True) as solver:
        nof_vars = solver.nof_vars() 
        nof_clauses = solver.nof_clauses() 

        # Call the solver for this formula:
        sat = solver.solve_limited()

        results[file_path] = [solver.time(), sat, nof_vars, nof_clauses]
        
def collect_files(folder_path, recursive=False):
    """
    Processes all files in the given folder (and optionally subfolders) matching the pattern.
    """
    if not os.path.isdir(folder_path):
        raise ValueError(f"The path {folder_path} is not a valid directory.")

    # Use glob to find files matching the pattern
    file_pattern = "*.cnf"
    search_pattern = os.path.join(folder_path, "**", file_pattern) if recursive else os.path.join(folder_path, file_pattern)
    files = glob.glob(search_pattern, recursive=recursive)

    if os.path.exists(OUTPUT_FILE) and os.path.isfile(OUTPUT_FILE):
        # Filter already done 
        computed_formulas = pd.read_csv(OUTPUT_FILE)['filename'].astype("string").values.tolist()
        files = list(filter(lambda f: f not in computed_formulas, files)) 

        # Re-add not computed 
        if SOLVE_TIMEOUT:
            timeout_formulas = pd.read_csv(OUTPUT_FILE)[['filename', 'sat', 'seconds']]
            timeout_formulas = timeout_formulas[(timeout_formulas['sat'].isna()) & (timeout_formulas['seconds'] < timeout)] 
            files.extend(timeout_formulas['filename'].astype("string").values.tolist())

    if not files:
        print("No files found matching the pattern.")
        return [] 
    else:
        return files 

def process_files_in_folder(folder_path, recursive=False, num_cores=4, timeout=60):
    files = collect_files(folder_path, recursive) 

    # Use a Manager dictionary to store results
    with Manager() as manager:
        results = manager.dict()
        # Initialize tqdm for progress tracking
        with tqdm.tqdm(total=len(files), desc="Processing files", unit="file") as pbar:
            # Callback function
            def task_done(future):
                try:
                    result = future.result()  # blocks until results are ready
                except TimeoutError as error:
                    pass 
                except Exception as error:
                    print("Function raised %s" % error)
                finally:
                    # Update progress bar 
                    pbar.update() 


            # Use a Pool to limit the number of cores
            with ProcessPool(max_workers=num_cores) as pool:
                for file_path in files:
                    results[file_path] = [timeout, None, None, None]

                    future = pool.schedule(process_cnf, [results, file_path], timeout=timeout)
                    future.add_done_callback(task_done)
                
        return dict(results) 


if __name__ == "__main__":
    folder_path = "formulas"
    recursive = True
    num_cores = 12  # Limit used cores
    timeout = 500  # Timeout for each file in seconds

    print(f"Folder is {folder_path}, the output will be saved in {OUTPUT_FILE}") 

    results = process_files_in_folder(folder_path, recursive, num_cores, timeout)

    df = pd.DataFrame.from_dict(results, orient="index").rename(columns={i:key for i,key in zip(range(4), ["seconds", "sat", "nof_vars", "nof_clauses"]) })
    print("New samples:", len(df)) 

    if os.path.exists(OUTPUT_FILE):
        solved = pd.read_csv(OUTPUT_FILE, index_col='filename') 
        df = pd.concat([solved, df], axis=0) 
        print("Total length is", len(df)) 

    df.to_csv(OUTPUT_FILE, index_label="filename", header=["seconds", "sat", "nof_vars", "nof_clauses"]) 
