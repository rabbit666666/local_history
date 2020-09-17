import itertools

def chunk_to_n_part(seq, size):
    return (seq[i::size] for i in range(size))

def chunk_every_to_n(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def join(tok, seq):
    seq = list(map(lambda x:str(x), seq))
    return tok.join(seq)
