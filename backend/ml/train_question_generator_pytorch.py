"""
PyTorch Sequence-to-Sequence Adaptive Question Generator with Attention
Trains an Encoder-Decoder neural network with Bahdanau attention
to generate tailored interview questions from candidate state representations.
"""

import json
import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from typing import List, Tuple, Dict

# Set deterministic random seed
torch.manual_seed(42)
random.seed(42)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Vocabulary:
    def __init__(self):
        self.word2idx = {"<PAD>": 0, "<SOS>": 1, "<EOS>": 2, "<UNK>": 3}
        self.idx2word = {0: "<PAD>", 1: "<SOS>", 2: "<EOS>", 3: "<UNK>"}
        self.n_words = 4

    def add_sentence(self, sentence: str):
        for word in sentence.lower().replace("?", " ?").replace(".", " .").replace(",", " ,").split():
            if word not in self.word2idx:
                self.word2idx[word] = self.n_words
                self.idx2word[self.n_words] = word
                self.n_words += 1

    def tokenize(self, sentence: str, max_len: int = 40) -> List[int]:
        tokens = [1]  # <SOS>
        for word in sentence.lower().replace("?", " ?").replace(".", " .").replace(",", " ,").split():
            tokens.append(self.word2idx.get(word, 3))
            if len(tokens) >= max_len - 1:
                break
        tokens.append(2)  # <EOS>
        # Pad
        while len(tokens) < max_len:
            tokens.append(0)
        return tokens[:max_len]


class EncoderRNN(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, embed_size: int = 64):
        super().__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(input_size, embed_size, padding_idx=0)
        self.gru = nn.GRU(embed_size, hidden_size, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, hidden_size)

    def forward(self, x):
        embedded = self.embedding(x)
        outputs, hidden = self.gru(embedded)
        # Combine bidirectional hidden states
        hidden = torch.tanh(self.fc(torch.cat((hidden[-2], hidden[-1]), dim=1))).unsqueeze(0)
        return outputs, hidden


class Attention(nn.Module):
    def __init__(self, hidden_size: int):
        super().__init__()
        self.attn = nn.Linear(hidden_size + hidden_size * 2, hidden_size)
        self.v = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, hidden, encoder_outputs):
        # hidden: (batch, hidden_size)
        # encoder_outputs: (batch, seq_len, hidden_size * 2)
        seq_len = encoder_outputs.size(1)
        hidden_expanded = hidden.unsqueeze(1).repeat(1, seq_len, 1)
        energy = torch.tanh(self.attn(torch.cat((hidden_expanded, encoder_outputs), dim=2)))
        attention = torch.softmax(self.v(energy).squeeze(2), dim=1)
        return attention.unsqueeze(1)


class AttnDecoderRNN(nn.Module):
    def __init__(self, hidden_size: int, output_size: int, embed_size: int = 64):
        super().__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.embedding = nn.Embedding(output_size, embed_size, padding_idx=0)
        self.attention = Attention(hidden_size)
        self.gru = nn.GRU(hidden_size * 2 + embed_size, hidden_size, batch_first=True)
        self.out = nn.Linear(hidden_size, output_size)

    def forward(self, input_step, hidden, encoder_outputs):
        embedded = self.embedding(input_step)
        attn_weights = self.attention(hidden[-1], encoder_outputs)
        context = torch.bmm(attn_weights, encoder_outputs)

        rnn_input = torch.cat((embedded, context), dim=2)
        output, hidden = self.gru(rnn_input, hidden)
        output = self.out(output.squeeze(1))
        return output, hidden, attn_weights


def train_seq2seq_generator():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    models_dir = base_dir / "saved_models"
    models_dir.mkdir(parents=True, exist_ok=True)

    with open(data_dir / "train.json", "r", encoding="utf-8") as f:
        train_data = json.load(f)

    with open(data_dir / "val.json", "r", encoding="utf-8") as f:
        val_data = json.load(f)

    src_vocab = Vocabulary()
    tgt_vocab = Vocabulary()

    for item in train_data + val_data:
        src_text = f"{item['role']} {item['target_competency']} {item['target_difficulty']} {item['previous_weakness']}"
        tgt_text = item["optimal_question"]
        src_vocab.add_sentence(src_text)
        tgt_vocab.add_sentence(tgt_text)

    print(f"Source Vocabulary Size: {src_vocab.n_words} | Target Vocabulary Size: {tgt_vocab.n_words}")

    # Prepare tensors
    X_train = []
    Y_train = []
    for item in train_data:
        src_text = f"{item['role']} {item['target_competency']} {item['target_difficulty']} {item['previous_weakness']}"
        X_train.append(src_vocab.tokenize(src_text, max_len=25))
        Y_train.append(tgt_vocab.tokenize(item["optimal_question"], max_len=25))

    X_train = torch.tensor(X_train, dtype=torch.long, device=device)
    Y_train = torch.tensor(Y_train, dtype=torch.long, device=device)

    hidden_size = 128
    encoder = EncoderRNN(src_vocab.n_words, hidden_size).to(device)
    decoder = AttnDecoderRNN(hidden_size, tgt_vocab.n_words).to(device)

    enc_optimizer = optim.Adam(encoder.parameters(), lr=0.001)
    dec_optimizer = optim.Adam(decoder.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss(ignore_index=0, reduction='sum')

    print("\n--- Training PyTorch Seq2Seq Question Generator (5 Epochs) ---")
    batch_size = 32
    num_batches = math.ceil(len(X_train) / batch_size)

    for epoch in range(1, 6):
        encoder.train()
        decoder.train()
        epoch_loss = 0.0
        total_tokens = 0

        for b in range(num_batches):
            x_batch = X_train[b * batch_size:(b + 1) * batch_size]
            y_batch = Y_train[b * batch_size:(b + 1) * batch_size]
            cur_bs = x_batch.size(0)

            enc_optimizer.zero_grad()
            dec_optimizer.zero_grad()

            encoder_outputs, hidden = encoder(x_batch)

            loss = torch.tensor(0.0, device=device)
            dec_input = torch.tensor([[1]] * cur_bs, dtype=torch.long, device=device)

            for t in range(1, y_batch.size(1)):
                output, hidden, _ = decoder(dec_input, hidden, encoder_outputs)
                target = y_batch[:, t]
                if (target != 0).any():
                    loss = loss + criterion(output, target)
                dec_input = target.unsqueeze(1)  # Teacher forcing

            valid_tokens = (y_batch[:, 1:] != 0).sum().item()
            if valid_tokens > 0:
                normalized_loss = loss / valid_tokens
                normalized_loss.backward()
                torch.nn.utils.clip_grad_norm_(encoder.parameters(), max_norm=1.0)
                torch.nn.utils.clip_grad_norm_(decoder.parameters(), max_norm=1.0)
                enc_optimizer.step()
                dec_optimizer.step()

                epoch_loss += loss.item()
                total_tokens += valid_tokens

        avg_loss = epoch_loss / max(total_tokens, 1)
        perplexity = math.exp(min(avg_loss, 20))
        print(f"Epoch {epoch}/5 - Cross-Entropy Loss: {avg_loss:.4f} | Perplexity: {perplexity:.2f}")



    # Save model weights & vocabularies as pure python dicts (pickle safe)
    checkpoint = {
        "encoder_state": encoder.state_dict(),
        "decoder_state": decoder.state_dict(),
        "src_word2idx": src_vocab.word2idx,
        "src_n_words": src_vocab.n_words,
        "tgt_word2idx": tgt_vocab.word2idx,
        "tgt_idx2word": tgt_vocab.idx2word,
        "tgt_n_words": tgt_vocab.n_words,
        "hidden_size": hidden_size
    }
    ckpt_path = models_dir / "pytorch_seq2seq_generator.pt"
    torch.save(checkpoint, ckpt_path)
    print(f"\nPyTorch Seq2Seq Question Generator model saved to: {ckpt_path}")


if __name__ == "__main__":
    train_seq2seq_generator()
