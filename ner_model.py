import torch
import torch.nn as nn
from pytorch_pretrained_bert import BertModel



class Net(nn.Module):
    def __init__(self, config, bert_state_dict, vocab_len, device='cuda'):
        super().__init__()
        self.bert = BertModel(config)
        self.num_layers = 2
        self.input_size = 768
        self.hidden_size = 768
        self.tagset_size = vocab_len
        # BERT always returns hidden_dim*2 dimensional representations. 
        if bert_state_dict is not None:
             self.bert.load_state_dict(bert_state_dict)
        self.bert.eval()
        # Each input has vector size 768, and outpus a vector size of 768//2.
        self.lstm = nn.LSTM(self.input_size, self.hidden_size//2, self.num_layers,
                            batch_first=True, bidirectional=True)
        self.fc = nn.Linear(self.hidden_size, vocab_len)
        self.device = device

    def init_hidden(self, batch_size):
        ''' Initializes hidden state '''
        # Create two new tensors with sizes n_layers x batch_size x hidden_dim,
        # initialized to zero, for hidden state and cell state of LSTM
        weight = next(self.parameters()).data
        
        if self.device == 'cuda':
            hidden = (nn.init.xavier_normal_(weight.new(self.num_layers * 2, batch_size, self.hidden_size//2).zero_()).cuda(),
                  nn.init.xavier_normal_(weight.new(self.num_layers * 2, batch_size, self.hidden_size//2).zero_()).cuda())
        else:
            hidden = (nn.init.xavier_normal_(weight.new(self.num_layers * 2, batch_size, self.hidden_size//2).zero_()),
                  nn.init.xavier_normal_(weight.new(self.num_layers * 2, batch_size, self.hidden_size//2).zero_()))
        
        return hidden

    def init_eval_hidden(self, batch_size):
        ''' Initializes hidden state '''
        # Create two new tensors with sizes n_layers x batch_size x hidden_dim,
        # initialized to zero, for hidden state and cell state of LSTM
        weight = next(self.parameters()).data
        
        hidden = (nn.init.xavier_normal_(weight.new(self.num_layers * 2, 1, self.hidden_size//2).zero_()),
                nn.init.xavier_normal_(weight.new(self.num_layers * 2, 1, self.hidden_size//2).zero_()))
        
        return hidden


    def forward(self, x, hidden):     
        with torch.no_grad():
            encoded_layers, _ = self.bert(x)
            enc = encoded_layers[-1]
        out, hidden = self.lstm(enc, hidden)
        logits = self.fc(out)
        # softmax = torch.nn.Softmax(dim=2)
        # logits = softmax(logits)
        y_hat = logits.argmax(-1)
        return logits, hidden, y_hat
