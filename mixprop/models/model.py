from typing import List, Union, Tuple

import numpy as np
from rdkit import Chem
import torch
import torch.nn as nn

from .mpn import MPN
from mixprop.args import TrainArgs
from mixprop.features import BatchMolGraph
from mixprop.nn_utils import get_activation_function, initialize_weights


class MoleculeModel(nn.Module):
    """A :class:`MoleculeModel` is a model which contains a message passing network following by feed-forward layers."""

    def __init__(self, args: TrainArgs):
        """
        :param args: A :class:`~mixprop.args.TrainArgs` object containing model arguments.
        """
        super(MoleculeModel, self).__init__()

        self.classification = args.dataset_type == 'classification'
        self.multiclass = args.dataset_type == 'multiclass'
        
        # when using cross entropy losses, no sigmoid or softmax during training. But they are needed for mcc loss.
        if self.classification or self.multiclass:
            self.no_training_normalization = args.loss_function in ['cross_entropy', 'binary_cross_entropy']

        self.output_size = args.num_tasks
        if self.multiclass:
            self.output_size *= args.multiclass_num_classes

        if self.classification:
            self.sigmoid = nn.Sigmoid()

        if self.multiclass:
            self.multiclass_softmax = nn.Softmax(dim=2)

        self.create_encoder(args)
        self.create_ffn(args)

        initialize_weights(self)

    def create_encoder(self, args: TrainArgs) -> None:
        """
        Creates the message passing encoder for the model.

        :param args: A :class:`~mixprop.args.TrainArgs` object containing model arguments.
        """
        self.encoder = MPN(args)
              
        if args.checkpoint_frzn is not None:
            if args.freeze_first_only: # Freeze only the first encoder
                for param in list(self.encoder.encoder.children())[0].parameters():
                    param.requires_grad=False
            else: # Freeze all encoders
                for param in self.encoder.parameters():
                    param.requires_grad=False                   
                        
    def create_ffn(self, args: TrainArgs) -> None:
        """
        Creates the feed-forward layers for the model.

        :param args: A :class:`~mixprop.args.TrainArgs` object containing model arguments.
        """
        self.multiclass = args.dataset_type == 'multiclass'
        if self.multiclass:
            self.num_classes = args.multiclass_num_classes
        if args.features_only:
            first_linear_dim = args.features_size
        else:
            if args.reaction_solvent:
                first_linear_dim = args.hidden_size + args.hidden_size_solvent
            else:
                first_linear_dim = args.hidden_size * args.number_of_molecules
            if args.use_input_features:
                first_linear_dim += args.features_size

        if args.atom_descriptors == 'descriptor':
            first_linear_dim += args.atom_descriptors_size

        dropout = nn.Dropout(args.dropout)
        activation = get_activation_function(args.activation)

        # Create FFN layers
        if args.ffn_num_layers == 1:
            ffn = [
                dropout,
                nn.Linear(first_linear_dim, self.output_size)
            ]
        else:
            ffn = [
                dropout,
                nn.Linear(601, args.ffn_hidden_size) #first_linear_dim, args.ffn_hidden_size) #first_linear_dim, args.ffn_hidden_size)
            ]
            for _ in range(args.ffn_num_layers - 2):
                ffn.extend([
                    activation,
                    dropout,
                    nn.Linear(args.ffn_hidden_size, args.ffn_hidden_size),
                ])
            ffn.extend([
                activation,
                dropout,
                nn.Linear(args.ffn_hidden_size, self.output_size),
            ])

        # If spectra model, also include spectra activation
        if args.dataset_type == 'spectra':
            if args.spectra_activation == 'softplus':
                spectra_activation = nn.Softplus()
            else: # default exponential activation which must be made into a custom nn module
                class nn_exp(torch.nn.Module):
                    def __init__(self):
                        super(nn_exp, self).__init__()
                    def forward(self, x):
                        return torch.exp(x)
                spectra_activation = nn_exp()
            ffn.append(spectra_activation)

        # Create FFN model
        self.ffn = nn.Sequential(*ffn)
        
        if args.checkpoint_frzn is not None:
            if args.frzn_ffn_layers >0:
                for param in list(self.ffn.parameters())[0:2*args.frzn_ffn_layers-2]: # Freeze weights and bias for given number of layers
                    print('FREEZING PARAM:',param)
                    param.requires_grad=False

    def fingerprint(self,
                  batch: Union[List[List[str]], List[List[Chem.Mol]], List[List[Tuple[Chem.Mol, Chem.Mol]]], List[BatchMolGraph]],
                  features_batch: List[np.ndarray] = None,
                  atom_descriptors_batch: List[np.ndarray] = None,
                  atom_features_batch: List[np.ndarray] = None,
                  bond_features_batch: List[np.ndarray] = None,
                  fingerprint_type = 'MPN') -> torch.FloatTensor:
        """
        Encodes the latent representations of the input molecules from intermediate stages of the model. 

        :param batch: A list of list of SMILES, a list of list of RDKit molecules, or a
                      list of :class:`~mixprop.features.featurization.BatchMolGraph`.
                      The outer list or BatchMolGraph is of length :code:`num_molecules` (number of datapoints in batch),
                      the inner list is of length :code:`number_of_molecules` (number of molecules per datapoint).
        :param features_batch: A list of numpy arrays containing additional features.
        :param atom_descriptors_batch: A list of numpy arrays containing additional atom descriptors.
        :param fingerprint_type: The choice of which type of latent representation to return as the molecular fingerprint. Currently 
                                 supported MPN for the output of the MPNN portion of the model or last_FFN for the input to the final readout layer.
        :return: The latent fingerprint vectors.
        """
        if fingerprint_type == 'MPN':
            return self.encoder(batch, features_batch, atom_descriptors_batch,
                                      atom_features_batch, bond_features_batch)
        elif fingerprint_type == 'last_FFN':
            
            
            embedding_combined = self.encoder(batch, features_batch, atom_descriptors_batch,
                               atom_features_batch, bond_features_batch)

            ### Obtain swapped output:
            # Obtain mol_frac1 and mol_frac2:
            T = embedding_combined[0:50,-1].view(-1,1) 
            mol_frac1 = embedding_combined[0:50,-2].view(-1,1)
            
            if torch.cuda.is_available():
                mol_frac2 = torch.ones(np.shape(mol_frac1),device='cuda')-mol_frac1
            else:
                mol_frac2 = torch.ones(np.shape(mol_frac1),device='cpu')-mol_frac1

            # Assign embeddings:
            embedding_shape = (50,300)

            embedding1 = embedding_combined[0:embedding_shape[0],0:embedding_shape[1]]
            embedding2 = embedding_combined[0:embedding_shape[0],embedding_shape[1]:-2]
            
            embedding_combined = torch.concat((embedding1*mol_frac1,embedding2*mol_frac2,T),axis=1)
            embedding_combined_swapped = torch.concat((embedding2*mol_frac2,embedding1*mol_frac1,T),axis=1)            
            
            fp12 = self.ffn[:-1](embedding_combined)
            fp21 = self.ffn[:-1](embedding_combined_swapped)
            
            fp_combined = torch.concat((fp12,fp21),axis=1)
#             print(np.shape(fp_combined))
            
            return fp_combined #fp12 #,fp21
            
#             return self.ffn[:-1](self.encoder(batch, features_batch, atom_descriptors_batch,
#                                             atom_features_batch, bond_features_batch))
        else:
            raise ValueError(f'Unsupported fingerprint type {fingerprint_type}.')

    def forward(self,
                batch: Union[List[List[str]], List[List[Chem.Mol]], List[List[Tuple[Chem.Mol, Chem.Mol]]], List[BatchMolGraph]],
                features_batch: List[np.ndarray] = None,
                atom_descriptors_batch: List[np.ndarray] = None,
                atom_features_batch: List[np.ndarray] = None,
                bond_features_batch: List[np.ndarray] = None) -> torch.FloatTensor:
        """
        Runs the :class:`MoleculeModel` on input.

        :param batch: A list of list of SMILES, a list of list of RDKit molecules, or a
                      list of :class:`~mixprop.features.featurization.BatchMolGraph`.
                      The outer list or BatchMolGraph is of length :code:`num_molecules` (number of datapoints in batch),
                      the inner list is of length :code:`number_of_molecules` (number of molecules per datapoint).
        :param features_batch: A list of numpy arrays containing additional features.
        :param atom_descriptors_batch: A list of numpy arrays containing additional atom descriptors.
        :param atom_features_batch: A list of numpy arrays containing additional atom features.
        :param bond_features_batch: A list of numpy arrays containing additional bond features.
        :return: The output of the :class:`MoleculeModel`, containing a list of property predictions
        """

        embedding_combined = self.encoder(batch, features_batch, atom_descriptors_batch,
                                       atom_features_batch, bond_features_batch)

        ## Format: A features file MUST be included containing mole fraction in the first column and temperature in the second column
        # Batch is also hard-coded here at 50,embedding size at 300
        # ffn size has been changed
        
        ### Obtain swapped output:
        # Obtain mol_frac1 and mol_frac2:
        T = embedding_combined[0:50,-1].view(-1,1) 
        mol_frac1 = embedding_combined[0:50,-2].view(-1,1) 
        if torch.cuda.is_available():
            mol_frac2 = torch.ones(np.shape(mol_frac1),device='cuda')-mol_frac1
        else:
            mol_frac2 = torch.ones(np.shape(mol_frac1),device='cpu')-mol_frac1
        
        # Assign embeddings:
        embedding_shape = (50,300)
        
        embedding1 = embedding_combined[0:embedding_shape[0],0:embedding_shape[1]]
        embedding2 = embedding_combined[0:embedding_shape[0],embedding_shape[1]:-2]
        
#         # Chas Mod: (Make sure ffn shape is default)
#         embedding_combined = torch.concat((embedding1,embedding2,mol_frac1),axis=1)
#         embedding_combined_swapped = torch.concat((embedding2,embedding1,mol_frac2),axis=1)
        
        # Mult Mod: (Must change ffn shape)
        embedding_combined = torch.concat((embedding1*mol_frac1,embedding2*mol_frac2,T),axis=1)
        embedding_combined_swapped = torch.concat((embedding2*mol_frac2,embedding1*mol_frac1,T),axis=1)
        
        output = self.ffn(embedding_combined)
        output_swapped = self.ffn(embedding_combined_swapped)
        
        output_combined = torch.mean(torch.concat((output,output_swapped),axis=1),axis=1).view(-1,1)
               
        # Don't apply sigmoid during training when using BCEWithLogitsLoss
        if self.classification and not (self.training and self.no_training_normalization):
            output = self.sigmoid(output)
        if self.multiclass:
            output = output.reshape((output.size(0), -1, self.num_classes))  # batch size x num targets x num classes per target
            if not (self.training and self.no_training_normalization):
                output = self.multiclass_softmax(output)  # to get probabilities during evaluation, but not during training when using CrossEntropyLoss

        return output_combined

    
    
    
    
#             ### Obtain swapped output:
#         # Obtain mol_frac1 and mol_frac2:
#         mol_frac1 = embedding_combined[0:50,-1].view(-1,1) 
#         mol_frac2 = torch.ones(np.shape(mol_frac1),device='cuda')-mol_frac1
        
#         # Assign embeddings:
#         embedding_shape = (np.shape(embedding_combined)[0],int(np.shape(embedding_combined)[1]/2))
        
#         embedding1 = embedding_combined[0:embedding_shape[0],0:embedding_shape[1]]
#         embedding2 = embedding_combined[0:embedding_shape[0],embedding_shape[1]:-1]
        
# #         # Chas Mod: (Make sure ffn shape is default)
# #         embedding_combined = torch.concat((embedding1,embedding2,mol_frac1),axis=1)
# #         embedding_combined_swapped = torch.concat((embedding2,embedding1,mol_frac2),axis=1)
        
#         # Mult Mod: (Must change ffn shape)
#         embedding_combined = torch.concat((embedding1*mol_frac1,embedding2*mol_frac2),axis=1)
#         embedding_combined_swapped = torch.concat((embedding2*mol_frac2,embedding1*mol_frac1),axis=1)
        
        
#         output = self.ffn(embedding_combined)
#         output_swapped = self.ffn(embedding_combined_swapped)
        
#         output_combined = torch.mean(torch.concat((output,output_swapped),axis=1),axis=1).view(-1,1)
               
#         # Don't apply sigmoid during training when using BCEWithLogitsLoss
#         if self.classification and not (self.training and self.no_training_normalization):
#             output = self.sigmoid(output)
#         if self.multiclass:
#             output = output.reshape((output.size(0), -1, self.num_classes))  # batch size x num targets x num classes per target
#             if not (self.training and self.no_training_normalization):
#                 output = self.multiclass_softmax(output)  # to get probabilities during evaluation, but not during training when using CrossEntropyLoss

#         return output_combined