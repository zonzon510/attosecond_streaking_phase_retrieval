import pickle
import numpy as np
import matplotlib.pyplot as plt
import tables
from scipy import interpolate
from proof import construct_proof
import matplotlib.patches as mpatches


def plot_elements(trace, proof_trace, xuv, xuv_envelope):

    fig = plt.figure(constrained_layout=False, figsize=(7, 5))
    gs = fig.add_gridspec(2, 2)

    ax = fig.add_subplot(gs[0, 0])
    ax.pcolormesh(trace, cmap='jet')
    ax.text(0, 0.9, '1', transform=ax.transAxes, backgroundcolor='yellow')

    ax = fig.add_subplot(gs[0, 1])
    ax.pcolormesh(proof_trace, cmap='jet')
    ax.text(0, 0.9, '2', transform=ax.transAxes, backgroundcolor='yellow')

    ax = fig.add_subplot(gs[1, 0])
    ax.plot(np.real(xuv), color='blue')
    ax.plot(np.abs(xuv), color='black', linestyle='dashed')
    ax.text(0, 0.9, '1', transform=ax.transAxes, backgroundcolor='yellow')

    ax = fig.add_subplot(gs[1, 1])
    ax.plot(np.real(xuv_envelope), color='blue')
    ax.plot(np.abs(xuv_envelope), color='black', linestyle='dashed')
    ax.text(0, 0.9, '2', transform=ax.transAxes, backgroundcolor='yellow')

    plt.show()


def process_xuv(xuv, xuv_time, f0, reduction, plotting=True):

    f0_removed = xuv * np.exp(-1j * 2 * np.pi * f0 * xuv_time)
    t_steps_reduced = len(xuv)/reduction
    time_reduced_dim = np.linspace(xuv_time[0], xuv_time[-1], t_steps_reduced)
    f = interpolate.interp1d(xuv_time, f0_removed, kind='cubic')
    xuv_reduced = f(time_reduced_dim)


    if plotting:
        fig, ax = plt.subplots(3, 1, figsize=(7, 10))

        ax[0].plot(xuv_time, np.real(xuv), color='blue')
        ax[0].plot(xuv_time, np.imag(xuv), color='red')
        ax[0].plot(xuv_time, np.abs(xuv), color='orange', linestyle='dashed')

        ax[1].plot(xuv_time, np.real(f0_removed), color='blue')
        ax[1].plot(xuv_time, np.imag(f0_removed), color='red')
        ax[1].plot(xuv_time, np.abs(f0_removed), color='orange', linestyle='dashed')

        axtwin = ax[1].twinx()
        axtwin.plot(xuv_time, np.unwrap(np.angle(f0_removed)), color='green', alpha=0.5)

        ax[2].plot(time_reduced_dim, np.real(xuv_reduced), color='blue')
        ax[2].plot(time_reduced_dim, np.imag(xuv_reduced), color='red')

        plt.show()

    return xuv_reduced



# open the pickles
try:
    with open('crab_tf_items.p', 'rb') as file:
        crab_tf_items = pickle.load(file)

    items = crab_tf_items['items']
    xuv_int_t = crab_tf_items['xuv_int_t']
    tmax = crab_tf_items['tmax']
    N = crab_tf_items['N']
    dt = crab_tf_items['dt']
    tauvec = crab_tf_items['tauvec']
    p_vec = crab_tf_items['p_vec']
    f0_ir = crab_tf_items['irf0']
    irEt = crab_tf_items['irEt']
    irtmat = crab_tf_items['irtmat']
    xuvf0 = crab_tf_items['xuvf0']


except Exception as e:
    print(e)
    print('run crab_tf.py first to pickle the needed files')
    exit(0)


if __name__ == "__main__":



    xuv_dimmension_reduction = 8

    # create a file for proof traces and xuv envelopes
    with tables.open_file('processed.hdf5', mode='w') as processed_data:

        processed_data.create_earray(processed_data.root, 'attstrace', tables.Float16Atom(),
                                     shape=(0, len(p_vec) * len(tauvec)))

        processed_data.create_earray(processed_data.root, 'proof', tables.Float16Atom(),
                                     shape=(0, len(p_vec) * len(tauvec)))

        processed_data.create_earray(processed_data.root, 'xuv', tables.ComplexAtom(itemsize=16),
                                     shape=(0, len(xuv_int_t)))

        processed_data.create_earray(processed_data.root, 'xuv_envelope', tables.ComplexAtom(itemsize=16),
                                     shape=(0, int(len(xuv_int_t)/xuv_dimmension_reduction)))





    with tables.open_file('attstrac_specific.hdf5', mode='r') as unprocessed_datafile:
        with tables.open_file('processed.hdf5', mode='a') as processed_data:

            index = 0
            # get the number of data points

            xuv = unprocessed_datafile.root.xuv_real[index, :] + 1j * unprocessed_datafile.root.xuv_imag[index, :]
            attstrace = unprocessed_datafile.root.trace[index, :].reshape(len(p_vec), len(tauvec))

            # construct proof trace
            proof_trace, _ = construct_proof(attstrace, tauvec=tauvec, dt=dt, f0_ir=f0_ir)

            # construct xuv pulse minus central oscilating term
            xuv_envelope = process_xuv(xuv, xuv_time=xuv_int_t, f0=xuvf0,
                                       reduction=xuv_dimmension_reduction, plotting=False)
            print('shape: ', np.shape(xuv_envelope))
            exit(0)

            # reduce dimmension of xuv envelope



            # plot_elements(attstrace, np.real(proof_trace), xuv, xuv_envelope)

            # append the data to the processed hdf5 file
            processed_data.root.attstrace.append(attstrace.reshape(1, -1))
            processed_data.root.proof.append(np.real(proof_trace).reshape(1, -1))
            processed_data.root.xuv.append(xuv.reshape(1, -1))
            processed_data.root.xuv_envelope.append(xuv_envelope.reshape(1, -1))




    # test opening the file
    index = 0
    with tables.open_file('processed.hdf5', mode='r') as processed_data:
        xuv1 = processed_data.root.xuv[index, :]
        xuv_envelope1 = processed_data.root.xuv_envelope[index, :]
        attstrace1 = processed_data.root.attstrace[index, :].reshape(len(p_vec), len(tauvec))
        proof_trace1 = processed_data.root.proof[index, :].reshape(len(p_vec), len(tauvec))

        plot_elements(attstrace1, np.real(proof_trace1), xuv1, xuv_envelope1)














