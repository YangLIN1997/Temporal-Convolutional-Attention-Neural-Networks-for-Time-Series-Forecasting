from __future__ import division
import numpy as np
import torch
import os
import logging
from torch.utils.data import DataLoader, Dataset, Sampler

logger = logging.getLogger('Transformer.Data')

class TrainDataset(Dataset):
    def __init__(self, data_path, data_name):
        self.data_name = data_name
        self.data = np.load(os.path.join(data_path, f'train_data_{data_name}.npy'))
        self.label = np.load(os.path.join(data_path, f'train_label_{data_name}.npy'))
        self.train_len = self.data.shape[0]
        logger.info(f'train_len: {self.train_len}')
        logger.info(f'building datasets from {data_path}...')

    def __len__(self):
        return self.train_len

    def __getitem__(self, index):
        return (self.data[index, :, :], self.label[index])

class ValidDataset(Dataset):
    def __init__(self, data_path, data_name):
        self.data_name = data_name
        self.data = np.load(os.path.join(data_path, f'valid_data_{data_name}.npy'))
        self.scale = np.load(os.path.join(data_path, f'valid_scale_{data_name}.npy'))
        self.mean = np.load(os.path.join(data_path, f'valid_mean_{data_name}.npy'))
        self.label = np.load(os.path.join(data_path, f'valid_label_{data_name}.npy'))
        self.train_len = self.data.shape[0]
        logger.info(f'valid_len: {self.train_len}')
        logger.info(f'building datasets from {data_path}...')

    def __len__(self):
        return self.train_len

    def __getitem__(self, index):
        if self.data_name != 'Sanyo' and self.data_name != 'Hanergy':
            id = self.data[index,0,-1].astype(int)
            return (self.data[index,:,:],self.scale[index],self.mean[index],self.label[index])
        else:
            return (self.data[index,:,:],self.scale,self.mean,self.label[index])

class TestDataset(Dataset):
    def __init__(self, data_path, data_name):
        self.data_name = data_name
        self.data = np.load(os.path.join(data_path, f'test_data_{data_name}.npy'))
        self.scale = np.load(os.path.join(data_path, f'test_scale_{data_name}.npy'))
        self.mean = np.load(os.path.join(data_path, f'test_mean_{data_name}.npy'))
        self.label = np.load(os.path.join(data_path, f'test_label_{data_name}.npy'))
        self.test_len = self.data.shape[0]
        logger.info(f'test_len: {self.test_len}')
        logger.info(f'building datasets from {data_path}...')

    def __len__(self):
        return self.test_len

    def __getitem__(self, index):
        if self.data_name != 'Sanyo' and self.data_name != 'Hanergy':
            id = self.data[index,0,-1].astype(int)
            return (self.data[index,:,:],self.scale[index],self.mean[index],self.label[index])
        else:
            return (self.data[index,:,:],self.scale,self.mean,self.label[index])

class WeightedSampler(Sampler):
    def __init__(self, data_path, data_name, replacement=True):
        v = np.load(os.path.join(data_path, f'train_scale_{data_name}.npy'))
        self.weights = torch.as_tensor(np.abs(v[:,0])/np.sum(np.abs(v[:,0])), dtype=torch.double)
        logger.info(f'weights: {self.weights}')
        self.num_samples = self.weights.shape[0]
        logger.info(f'num samples: {self.num_samples}')
        self.replacement = replacement

    def __iter__(self):
        return iter(torch.multinomial(self.weights, self.num_samples, self.replacement).tolist())

    def __len__(self):
        return self.num_samples