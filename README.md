This code uses the PyTorch Geometric library to predict CaDiCaL runtimes using various Graph Neural Networks (GNNs).

To create the dataset, run the 'gen-data' script to generate random 3-SAT instances. Then, execute the 'compute-times-parallel' script to compute and store the actual CaDiCaL solving runtimes in a CSV file.

To transform CNF formulas into graphs, you can use either LIG or LCG encoding.
The corresponding implementations, along with the GNN training process, are provided in the Jupyter Notebooks.
