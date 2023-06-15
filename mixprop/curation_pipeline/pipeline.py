import warnings
import time
import os
from pathlib import Path

from .load_data import load_data
from .split_data import split_nist_dippr
from .remove_salts import remove_salts
from .remove_not_liquid import remove_not_liquid
from .T_logV_correlation import drop_flagged_data
from .remove_inconsistent import remove_inconsistent
from .pchip_interpolation import pchip_interpolation
from .write_data import write_data


warnings.filterwarnings("ignore")


def prepare_dataset(input_args):
    """
    Wrapper for data curation pipeline.
    """

    start = time.time()

    add_paths_to_args(input_args)
    
    print("Loading Data: ---")
    nist_knovel_all = load_data(input_args)
    print("Time Elapsed: {:.2f}".format(time.time() - start))

    print("Splitting Data: ---")
    test_mols = split_nist_dippr(nist_knovel_all, input_args)
    print("Total Time Elapsed: {:.2f}".format(time.time() - start))

    print("Removing Salts: ---")
    nist_knovel_all = remove_salts(nist_knovel_all, test_mols)
    print("Total Time Elapsed: {:.2f}".format(time.time() - start))

    print("Removing Non-Liquid Compounds: ---")
    nist_knovel_all = remove_not_liquid(nist_knovel_all,test_mols,input_args)
    print("Time Elapsed: {}".format(time.time()-start))

    print("Removing Compounds Based on Viscosity/Temperature Correlation: ---")
    nist_knovel_all = drop_flagged_data(nist_knovel_all, test_mols)
    print("Total Time Elapsed: {:.2f}".format(time.time() - start))

    print("Removing Inconsistent Data: ---")
    nist_knovel_all = remove_inconsistent(nist_knovel_all, test_mols, input_args)
    print("Total Time Elapsed: {:.2f}".format(time.time() - start))

    print("Combining Data using PCHIP Interpolation: ---")
    nist_knovel_all = pchip_interpolation(nist_knovel_all, test_mols)
    print("Total Time Elapsed: {}".format(time.time() - start))

    print("Writing Dataset to {}: ---".format(input_args["out_path"]))
    write_data(nist_knovel_all, test_mols, input_args)

    print("Total Time Elapsed: {:.2f}".format(time.time() - start))

# def load_model(args):
#     if 'checkpoint_dir' in args.keys():
#         return mixprop_model(args['checkpoint_dir'])
#     else:
#         path = str(Path(__file__).absolute())
#         path = '/'.join(path.split('/')[:-1])
#         checkpoint_dir = os.path.join(path,'pretrained_models/nist_dippr_model/nist_dippr_model')
        
#         print('Loading models from {}'.format(checkpoint_dir))
        
#         return mixprop_model(checkpoint_dir)

# curation_args = {
#     "NIST": "pretrained_models/nist_dippr_source/NIST_Visc_Data.csv",  # Path to NIST data
#     "DIPPR": "pretrained_models/nist_dippr_source/logV_bp_mp.csv",  # Path to DIPPR data
#     "bp_pred_path": "pretrained_models/bp_data/bp_pred.csv",  # Path to boiling point data (already predicted)
#     "mp_pred_path": "pretrained_models/mp_data/mp_pred.csv",  # Path to melting point data (already predicted)
#     "dummy_mol": "CCO",  # Dummy compound for mixing in DIPPR pure component data
#     "dippr_ref_T": 298,  # DIPPR temperature
#     "test_split": 0.2,  # Fraction to hold out for testing
#     "thresh_pure": 0.025,  # Settings for inconsistent pure data screening
#     "thresh_logV": 0.5,  # Settings for inconsistent pure data screening
#     "out_path":"." # Location for files to be written to
# }

def add_paths_to_args(args):
    path = str(Path(__file__).absolute())
    path = '/'.join(path.split('/')[:-2])
    source_path = os.path.join(path,'pretrained_models')

    if 'NIST' not in args.keys():
        nist_path = os.path.join(source_path,'nist_dippr_source/NIST_Visc_Data.csv')
        args['NIST'] = nist_path
        print(print('Loading data from {}'.format(nist_path)))

    if 'DIPPR' not in args.keys():
        dippr_path = os.path.join(source_path,'nist_dippr_source/logV_bp_mp.csv')
        args['DIPPR'] = dippr_path
        print(print('Loading data from {}'.format(dippr_path)))
 
    if 'bp_pred_path' not in args.keys():
        bp_path = os.path.join(source_path,'bp_data/bp_pred.csv')
        args['bp_pred_path'] = bp_path
        print(print('Loading data from {}'.format(bp_path)))

    if 'mp_pred_path' not in args.keys():
        mp_path = os.path.join(source_path,'mp_data/mp_pred.csv')
        args['mp_pred_path'] = mp_path
        print(print('Loading data from {}'.format(mp_path)))
        
    return args
    
