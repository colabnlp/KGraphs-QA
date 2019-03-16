import numpy as np 
from torch.utils import data 
import parameters
import torch 
from pytorch_pretrained_bert import BertTokenizer

device = 'cpu'

class HParams:
    def __init__(self, vocab_type):
        self.VOCAB_DICT = {
            'bc5cdr': ('<PAD>', 'B-Chemical', 'O', 'B-Disease' , 'I-Disease', 'I-Chemical'),
            'i2b2' : ('<PAD>', 'treatment', '+treatment', 'test', '+test', 'problem', '+problem', 'O'),
            'relations' : ('<PAD>','TrCP', 'TeCP', 'TrWP', 'TeRP', 'PIP', 'TrAP', 'TrIP', 'TrNAP', 'None')
        }
        self.VOCAB = self.VOCAB_DICT[vocab_type]
        self.tag2idx = {v:k for k,v in enumerate(self.VOCAB)}
        self.idx2tag = {k:v for k,v in enumerate(self.VOCAB)}

        self.batch_size = 2
        self.lr = 0.0001
        self.n_epochs = 30 
        self.hidden_size = 384

        self.tokenizer = BertTokenizer(vocab_file=parameters.VOCAB_FILE, do_lower_case=False)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'


class NerDataset(data.Dataset):
    def __init__(self, path, vocab_type):
        self.hp = HParams(vocab_type)
        instances = open(path).read().strip().split('\n\n\n\n\n')
        sents = []
        tags_li = []
        for entry in instances:
            words = [line.split()[0] for line in entry.splitlines()]
            tags = ([line.split()[-1] for line in entry.splitlines()])
            sents.append(["[CLS]"] + words + ["[SEP]"])
            tags_li.append(["<PAD>"] + tags + ["<PAD>"])
        self.sents, self.tags_li = sents, tags_li

    def __len__(self):
        return len(self.sents)


    def __getitem__(self, idx):
        words, tags = self.sents[idx], self.tags_li[idx] # words, tags: string list

        # We give credits only to the first piece.
        x, y = [], [] # list of ids
        is_heads = [] # list. 1: the token is the first piece of a word
        for w, t in zip(words, tags):
            tokens = self.hp.tokenizer.tokenize(w) if w not in ("[CLS]", "[SEP]") else [w]
            xx = self.hp.tokenizer.convert_tokens_to_ids(tokens)

            is_head = [1] + [0]*(len(tokens) - 1)

            t = [t] + ["<PAD>"] * (len(tokens) - 1)  # <PAD>: no decision
            yy = [self.hp.tag2idx[each] for each in t]  # (T,)

            x.extend(xx)
            is_heads.extend(is_head)
            y.extend(yy)

        assert len(x)==len(y)==len(is_heads), f"len(x)={len(x)}, len(y)={len(y)}, len(is_heads)={len(is_heads)}"
        # seqlen
        seqlen = len(y)

        # to string
        words = " ".join(words)
        tags = " ".join(tags)
        return words, x, is_heads, tags, y, seqlen


class RelationDataset(data.Dataset):
    def __init__(self, path, vocab_type):
        self.hp = HParams(vocab_type)
        instances = open(path).read().strip().split('\n')
        sents = []
        tags_li = []
        for entry in instances:
            words = [line.split()[0] for line in entry.splitlines()]
            tags = ([line.split()[-1] for line in entry.splitlines()])
            sents.append(["[CLS]"] + words + ["[SEP]"])
            tags_li.append(["<PAD>"] + tags + ["<PAD>"])
        self.sents, self.tags_li = sents, tags_li

    def __len__(self):
        return len(self.sents)


    def __getitem__(self, idx):
        words, tags = self.sents[idx], self.tags_li[idx] # words, tags: string list

        # We give credits only to the first piece.
        x, y = [], [] # list of ids
        is_heads = [] # list. 1: the token is the first piece of a word
        for w, t in zip(words, tags):
            tokens = self.hp.tokenizer.tokenize(w) if w not in ("[CLS]", "[SEP]") else [w]
            xx = self.hp.tokenizer.convert_tokens_to_ids(tokens)

            is_head = [1] + [0]*(len(tokens) - 1)

            t = [t] + ["<PAD>"] * (len(tokens) - 1)  # <PAD>: no decision
            yy = [self.hp.tag2idx[each] for each in t]  # (T,)

            x.extend(xx)
            is_heads.extend(is_head)
            y.extend(yy)

        assert len(x)==len(y)==len(is_heads), f"len(x)={len(x)}, len(y)={len(y)}, len(is_heads)={len(is_heads)}"
        # seqlen
        seqlen = len(y)

        # to string
        words = " ".join(words)
        tags = " ".join(tags)
        return words, x, is_heads, tags, y, seqlen


def pad(batch):
    '''Pads to the longest sample'''
    f = lambda x: [sample[x] for sample in batch]
    words = f(0)
    is_heads = f(2)
    tags = f(3)
    seqlens = f(-1)
    maxlen = np.array(seqlens).max()

    f = lambda x, seqlen: [sample[x] + [0] * (seqlen - len(sample[x])) for sample in batch] # 0: <pad>
    x = f(1, maxlen)
    y = f(-2, maxlen)

    f = torch.LongTensor

    return words, f(x), is_heads, tags, f(y), seqlens