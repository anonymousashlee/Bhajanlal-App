#!/usr/bin/env python3
"""Tiny decoder-only transformer (byte-level GPT) for the Bhajanlal POC.

Real architecture: learned token + positional embeddings, causal multi-head
self-attention, FFN, residual connections, final layer norm + tied-ish head.
This is a genuine language model trained with genuine gradient descent.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
from torch.nn import functional as F

VOCAB = 256          # byte-level vocabulary
BLOCK = 128          # context length
N_LAYER = 4
N_HEAD = 4
N_EMBD = 128


class Head(nn.Module):
    def __init__(self):
        super().__init__()
        self.q = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.k = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.v = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.register_buffer("mask", torch.tril(torch.ones(BLOCK, BLOCK)))

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.q(x), self.k(x), self.v(x)
        q = q.view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        k = k.view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        v = v.view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(k.size(-1))
        att = att.masked_fill(self.mask[:T, :T] == 0, float("-inf"))
        att = F.softmax(att, dim=-1)
        return (att @ v).transpose(1, 2).contiguous().view(B, T, C)


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1 = nn.LayerNorm(N_EMBD)
        self.att = Head()
        self.ln2 = nn.LayerNorm(N_EMBD)
        self.ffn = nn.Sequential(
            nn.Linear(N_EMBD, 4 * N_EMBD), nn.GELU(),
            nn.Linear(4 * N_EMBD, N_EMBD),
        )

    def forward(self, x):
        x = x + self.att(self.ln1(x))
        return x + self.ffn(self.ln2(x))


class TinyGPT(nn.Module):
    def __init__(self):
        super().__init__()
        self.tok = nn.Embedding(VOCAB, N_EMBD)
        self.pos = nn.Embedding(BLOCK, N_EMBD)
        self.blocks = nn.Sequential(*[Block() for _ in range(N_LAYER)])
        self.ln = nn.LayerNorm(N_EMBD)
        self.head = nn.Linear(N_EMBD, VOCAB, bias=False)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        _, t = idx.shape
        pos = torch.arange(t, device=idx.device)
        x = self.tok(idx) + self.pos(pos)
        x = self.blocks(x)
        logits = self.head(self.ln(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, VOCAB), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new, temperature=0.8):
        for _ in range(max_new):
            idx_c = idx[:, -BLOCK:]
            logits, _ = self(idx_c)
            logits = logits[:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            nxt = torch.multinomial(probs, 1)
            idx = torch.cat((idx, nxt), dim=1)
        return idx
