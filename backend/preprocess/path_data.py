import numpy as np
import pickle
import argparse
import os
DATA_PATH = ".."
def get_node_number(inPath, outputPath):
    examples = pickle.load(open(inPath + "stat", 'rb'))
    examples = examples[0].astype(int)
    np.save(outputPath+"y.npy", examples)

def path_row_col(inPath, fileName, outputPath):
    examples = pickle.load(open(inPath+fileName, 'rb'))
    # A = np.array([examples[:, 0], examples[:, 2]])
    A = np.array([examples[:, 0], examples[:, 2], examples[:, 3]])
    A = A.astype(int)
    np.save(outputPath+'edge_index.npy', A)

# 验证
def read_npy_file(readFile):
    # read file.npy
    output_data = np.load(readFile)
    print(output_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build path_data numpy files for CTpath datasets")
    parser.add_argument(
        "--datasets",
        type=str,
        default="ICEWS14",
        help="Comma-separated dataset names under ../data (e.g. ICEWS14,CHRONIC)",
    )
    args = parser.parse_args()

    for data_name in [x.strip() for x in args.datasets.split(",") if x.strip()]:
        inpath = f"{DATA_PATH}/data/{data_name}/"
        outputPath = f"{DATA_PATH}/path_data/{data_name}/"
        os.makedirs(outputPath, exist_ok=True)
        fileName = "train.pickle"
        get_node_number(inpath, outputPath)
        path_row_col(inpath, fileName, outputPath)
        # valid
        read_npy_file(outputPath + "y.npy")
        # read_npy_file(outputPath + "edge_index.npy")
