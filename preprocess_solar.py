from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import numpy as np
import h5py
from scipy import stats
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def prep_data(data, data_mean, data_scale, task='search_', name='train', data2=None):
    input_size = window_size - stride_size
    time_len = data.shape[0]
    total_windows = n_id * (time_len - input_size) // stride_size
    print("windows pre: ", total_windows, "   No of days:", total_windows / n_id)
    # if train: windows_per_series -= (stride_size-1) // stride_size
    x_input = np.zeros((total_windows, window_size, num_covariates), dtype='float32')
    label = np.zeros((total_windows, window_size), dtype='float32')
    for i in range(total_windows // n_id):
        window_start = stride_size * i
        window_end = window_start + window_size
        x_input[i * n_id:(i + 1) * n_id, 0, 0] = (x_input[i * n_id:(i + 1) * n_id, 0, 0] - data_mean) / data_scale
        x_input[i * n_id:(i + 1) * n_id, 1:, 0] = data[window_start:window_end - 1, :, 0].swapaxes(0, 1).reshape(-1,
                                                                                                                 window_size - 1)
        x_input[i * n_id:(i + 1) * n_id, :, 1:] = data[window_start:window_end, :, 1:].swapaxes(0, 1).reshape(-1,
                                                                                                              window_size,
                                                                                                              num_covariates - 1)
        label[i * n_id:(i + 1) * n_id, :] = data[window_start:window_end, :, 0].swapaxes(0, 1).reshape(-1, window_size)
    zeros_index = np.zeros(x_input.shape[0])
    for i in range(window_size // stride_size):
        var = np.var(x_input[:, i * stride_size + 1:(i + 1) * stride_size, 0] * data_scale[
            x_input[:, 0, -1].astype(np.int)].reshape(-1, 1) + data_mean[x_input[:, 0, -1].astype(np.int)].reshape(-1,
                                                                                                                   1),
                     axis=1)
        zeros_index += (var < 1e-3)
    zeros_index = np.where((zeros_index > 0))[0]
    x_input = np.delete(x_input, zeros_index, axis=0)
    label = np.delete(label, zeros_index, axis=0)
    print('x_input', x_input.shape)
    # x = np.arange(window_size)
    # if zeros_index.shape[0]>0:
    #     f = plt.figure()
    #     plt.plot(x, x_input[zeros_index[0].astype(np.int), :, 0] * data_scale[x_input[zeros_index[0].astype(np.int), :, -1].astype(np.int) ] + data_mean[x_input[zeros_index[0].astype(np.int), :, -1].astype(np.int) ], color='b')
    #     f.savefig(name+save_name + '_visual_removed.png')
    #     plt.close()
    if data2 is not None:
        time_len = data2.shape[0]
        total_windows = n_id * (time_len - input_size) // stride_size
        print("windows pre2: ", total_windows, "   No of days:", total_windows / n_id)
        # if train: windows_per_series -= (stride_size-1) // stride_size
        x_input2 = np.zeros((total_windows, window_size, num_covariates), dtype='float32')
        label2 = np.zeros((total_windows, window_size), dtype='float32')
        for i in range(total_windows // n_id):
            window_start = stride_size * i
            window_end = window_start + window_size
            x_input2[i * n_id:(i + 1) * n_id, 0, 0] = (x_input2[i * n_id:(i + 1) * n_id, 0, 0] - data_mean) / data_scale
            x_input2[i * n_id:(i + 1) * n_id, 1:, 0] = data2[window_start:window_end - 1, :, 0].swapaxes(0, 1).reshape(
                -1, window_size - 1)
            x_input2[i * n_id:(i + 1) * n_id, :, 1:] = data2[window_start:window_end, :, 1:].swapaxes(0, 1).reshape(-1,
                                                                                                                    window_size,
                                                                                                                    num_covariates - 1)
            label2[i * n_id:(i + 1) * n_id, :] = data2[window_start:window_end, :, 0].swapaxes(0, 1).reshape(-1,
                                                                                                             window_size)
        zeros_index = np.zeros(x_input2.shape[0])
        for i in range(window_size // stride_size):
            var = np.var(x_input2[:, i * stride_size + 1:(i + 1) * stride_size, 0] * data_scale[
                x_input2[:, 0, -1].astype(np.int)].reshape(-1, 1) + data_mean[
                             x_input2[:, 0, -1].astype(np.int)].reshape(-1, 1), axis=1)
            zeros_index += (var < 1e-3)
        zeros_index = np.where((zeros_index > 0))[0]
        x_input2 = np.delete(x_input2, zeros_index, axis=0)
        label2 = np.delete(label2, zeros_index, axis=0)

        x_input = np.concatenate((x_input, x_input2), axis=0)
        label = np.concatenate((label, label2), axis=0)

    prefix = os.path.join(save_path, name + '_')
    np.save(prefix + 'data_' + task + save_name, x_input)
    print(prefix + 'data_' + task + save_name, x_input.shape)
    np.save(prefix + 'mean_' + task + save_name, data_mean[x_input[:, 0, -1].astype(np.int)])
    np.save(prefix + 'scale_' + task + save_name, data_scale[x_input[:, 0, -1].astype(np.int)])
    np.save(prefix + 'label_' + task + save_name, label)


def prepare(task='search_'):
    covariates = gen_covariates(data_frame[train_start:test_end].index, num_covariates, n_id)
    train_data1 = covariates[:data_frame[:train_end].shape[0]].copy()
    valid_data = covariates[data_frame[:valid_start].shape[0] - 1:data_frame[:valid_end].shape[0]].copy()
    test_data = covariates[data_frame[:test_start].shape[0] - 1:data_frame[:test_end].shape[0]].copy()

    valid_data[:, :, 0] = data_frame[valid_start:valid_end].copy()
    test_data[:, :, 0] = data_frame[test_start:test_end].copy()
    train_data1[:, :, 0] = data_frame[train_start:train_end].copy()
    train_data = train_data1

    # Standardlize data
    data_scale = np.zeros(n_id)
    data_mean = np.zeros(n_id)

    for i in range(n_id):
        st_scaler = StandardScaler()
        st_scaler.fit(train_data[data_start[i]:, i, 0].reshape(-1,1))
        train_data[:, i, 0] = st_scaler.transform(train_data[:, i, 0].reshape(-1,1)).reshape(-1,)
        valid_data[:, i, 0] = st_scaler.transform(valid_data[:, i, 0].reshape(-1,1)).reshape(-1,)
        test_data[:, i, 0] = st_scaler.transform(test_data[:, i, 0].reshape(-1,1)).reshape(-1,)
        data_scale[i] = st_scaler.scale_[0]
        data_mean[i] = st_scaler.mean_[0]
    # Prepare data
    # prep_data(train_data[0:480], data_mean, data_scale, task, name='train', data2 = train_data[0:480])
    # prep_data(train_data[:train_data1.shape[0]], data_mean, data_scale, task, name='train', data2 = train_data[train_data1.shape[0]:])
    prep_data(train_data, data_mean, data_scale, task, name='train', data2=None)
    prep_data(valid_data, data_mean, data_scale, task, name='valid', data2=None)
    prep_data(test_data, data_mean, data_scale, task, name='test', data2=None)


def visualize(data, day_start, day_num, save_name):
    x = np.arange(stride_size * day_num)
    f = plt.figure()
    plt.plot(x, data[day_start * stride_size:day_start * stride_size + stride_size * day_num].values[:, 4], color='b')
    f.savefig('visual_' + save_name + '.png')
    plt.close()


def gen_covariates(times, num_covariates, n_id):
    covariates = np.zeros((times.shape[0], n_id, num_covariates))
    for i, input_time in enumerate(times):
        covariates[i, :, 1] = input_time.hour
        covariates[i, :, 2] = input_time.month
    for i in range(n_id):
        covariates[:, i, -1] = i
        cov_age = np.zeros((times.shape[0],))
        cov_age[data_start[i]:] = stats.zscore(np.arange(times.shape[0] - data_start[i]))
        covariates[:, i, 3] = cov_age
    for i in range(1,num_covariates-1):
        covariates[:,:,i] = stats.zscore(covariates[:,:,i])
    return covariates


if __name__ == '__main__':

    global save_path
    save_name = 'Solar'
    window_size = 24*2
    stride_size = 24
    pred_days = 1
    given_days = 1
    num_covariates = 5
    train_ratio = 0.85
    valid_ratio = 0.05
    test_ratio = 0.05

    save_path = os.path.join('data', save_name)
    data_path = os.path.join(save_path, 'Data.csv.zip')
    data_frame = pd.read_csv(data_path)

    data_frame = data_frame.set_index(pd.to_datetime(data_frame['LocalTime']))
    input_size = window_size-stride_size

    data_frame = data_frame.resample('1H', label='left', closed='left').mean()
    print('From: ',data_frame.index[0],'to: ',data_frame.index[-1])
    visualize(data_frame, 50, day_num=10, save_name = save_name)
    n_id = data_frame.shape[1]
    n_day = data_frame.shape[0]/stride_size
    print('total days:', n_day)
    print('total samples:', data_frame.shape[0])
    print('total series:', data_frame.shape[1])
    data_start = (data_frame.values!=0).argmax(axis=0) #find first nonzero value in each time series
    data_start = (data_start // stride_size) * stride_size

    # For gridsearch
    train_start = '2006-01-01 00:00:00'
    train_end = '2006-08-10 23:00:00'
    valid_start = '2006-08-10 00:00:00' #need additional 7 days as given info
    valid_end = '2006-08-17 23:00:00'
    test_start = '2006-08-17 00:00:00' #need additional 7 days as given info
    test_end = '2006-08-24 23:00:00'
    train_start2 = '2006-08-31 00:00:00'
    train_end2 = '2006-12-31 23:00:00'
    prepare(task='search_')

    # For inference
    train_start = '2006-01-01 00:00:00'
    train_end = '2006-08-17 23:00:00'
    # train_end = '2006-08-24 23:00:00'
    valid_start = '2006-08-17 00:00:00' #need additional 7 days as given info
    valid_end = '2006-08-24 23:00:00'
    test_start = '2006-08-24 00:00:00' #need additional 7 days as given info
    test_end = '2006-08-31 23:00:00'
    train_start2 = '2006-08-31 00:00:00'
    train_end2 = '2006-12-31 23:00:00'
    prepare(task='')