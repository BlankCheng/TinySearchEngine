from tqdm import tqdm
from glob import glob
import argparse
import os
import pypeln.process as pr


parser = argparse.ArgumentParser()
parser.add_argument(
    '--token_dir',
    default='data',
    type=str,
    help='token dir'
)
parser.add_argument(
    '--output_dir',
    default='perm',
    type=str,
    help='output dir of perm'
)
args = parser.parse_args()
os.makedirs(args.output_dir, exist_ok=False)

count_file = glob(os.path.join(args.token_dir, 'num_tokens.txt'))[0]
token_files = glob(os.path.join(args.token_dir, 'tokens_info_[0-9,a-z].txt'))
n_tokens = 0
with open(count_file, 'r') as input:
    n_tokens = int(input.readline().strip('\n'))

def perm_fn(token):
    perm_results = [token]
    for _ in range(len(token) - 1):
        token = token[-1] + token[:-1]
        perm_results.append(token)
    return perm_results


def worker(token_file):
    """
    read row: <TOKEN>-<file_num>-<N>-*
    write row: <PERM>-<ORIG>-<file_num>-<N>-*
    """
    f = open(token_file, 'r')
    base_name = os.path.split(token_file)[-1]
    g = open(os.path.join(args.output_dir, f'temp_{base_name}'), 'w')
    rows = f.readlines()
    results = []
    for row in rows:
        token, *rest = row.split('-')
        perm_results = perm_fn(f'{token}$')
        results.extend(['-'.join([perm, token, *rest]) for perm in perm_results])
    results.sort(key=lambda x: x.split('-')[0])
    g.writelines(results)
    f.close()
    g.close()
    return token_file, len(rows), len(results)
total_perm = 0
with tqdm(total=n_tokens, ncols=80, desc='Write to temp files') as pbar:
    for token_file, n_part, n_perm in pr.map(
            worker, token_files, workers=1, maxsize=10):
        total_perm += n_perm
        pbar.update(n_part)

# k-way merge
tmp_files = glob(os.path.join(args.output_dir, 'temp*.txt'))
handlers = [open(file, 'r') for file in tmp_files]
n_non_empty = len(handlers)
k_postings = [
    [idx, handler.readline()]\
        for idx, handler in enumerate(handlers)
]
k_postings.sort(key=lambda x: x[1].split('-')[0], reverse=True)
prefix = k_postings[-1][1][0]
sorted_perm_results = []
counter = 0
with tqdm(total=total_perm, ncols=80, desc='Merge') as pbar:
    while n_non_empty:
        k_postings.sort(key=lambda x: x[1].split('-')[0], reverse=True)
        idx, posting = k_postings.pop()
        if posting[0] != prefix or len(sorted_perm_results) > 1e6:
            with open(f'{args.output_dir}/perm_token_info_{prefix}.txt', 'a') as output:
                output.writelines(sorted_perm_results)
                pbar.update(len(sorted_perm_results))
            if posting[0] != prefix:
                with open(f'{args.output_dir}/perm_token_info_{prefix}_count.txt', 'a') as output:
                    output.write(str(counter))
                    counter = 0
            sorted_perm_results = []
        sorted_perm_results.append(posting)
        counter += 1
        new_posting = handlers[idx].readline()
        if not len(new_posting):
            n_non_empty -= 1
            continue
        k_postings.append([idx, new_posting])
        prefix = posting[0]
    if len(sorted_perm_results):
        with open(f'{args.output_dir}/perm_token_info_{prefix}.txt', 'a') as output:
            output.writelines(sorted_perm_results)
            pbar.update(len(sorted_perm_results))
        with open(f'{args.output_dir}/perm_token_info_{prefix}_count.txt', 'a') as output:
            output.write(str(counter))
            counter = 0
    

for idx, handler in enumerate(handlers):
    handler.close()
    os.system(f'rm -f {tmp_files[idx]}')