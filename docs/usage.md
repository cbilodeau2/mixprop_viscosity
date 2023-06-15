## 1. Download Models:

To use mixprop in a project, first download the pretrained models from Zenodo:

```
from mixprop.visc_pred_wrapper import download_models
download_models()
```
Files will be downloaded into your current directory.

## 2. Calculate Predictions:

There are four types of inputs that you can provide to mixprop, depending on the type of input you would like to use. Input arguments are formatted as a dictionary, for example:

```
# Input Arguments:
args = {'smi1': 'O',
        'smi2': 'c1ccccc1',
        'molfrac1': 0.25,
        'T': 298,
        'n_models':25,
        'threshold':0.022,
        'num_workers':4,
        'check_phase':False,
        'checkpoint_dir': 'pretrained_models/nist_dippr_model/nist_dippr_model',
        'input_path':'examples/example_input.csv',
        }
```

### 2.1. Make a prediction for a single datapoint.

```
# Usage:
# out = [viscosity (cp), reliability (bool)]

from mixprop.visc_pred_wrapper import visc_pred_single

out = visc_pred_single(args)

print('Viscosity = {} cP'.format(out[0]))
print('Reliability = {}'.format(out[1]))
```

### 2.2. Make a prediction for a given pair of molecules at a range of temperatures at a fixed mole fraction.
*Note: Any temperature input will be ignored.

```
# Usage:
# out = [viscosity (cp), temperature (K), reliability (bool)]

from mixprop.visc_pred_wrapper import visc_pred_T_curve
import matplotlib.pyplot as plt

out = visc_pred_T_curve(args)

plt.figure(figsize=(3,3),dpi=100)
plt.plot(out[1],out[0],marker='o')
plt.xlabel('Temperature (K)')
plt.ylabel('Viscosity (cP)')
plt.show()
```

### 2.3. Make a prediction for a given pair of molecules at a range of mole fractions, but at a fixed temperature.
*Note: Any mole fraction input will be ignored.

```
# Usage:
# out = [viscosity (cp), mole fraction, reliability (bool)]

from mixprop.visc_pred_wrapper import visc_pred_molfrac1_curve
import matplotlib.pyplot as plt

out = visc_pred_molfrac1_curve(args)

plt.figure(figsize=(3,3),dpi=100)
plt.plot(out[1],out[0],marker='o')
plt.xlabel('Mole Fraction')
plt.ylabel('Viscosity (cP)')
plt.show()
```

### 2.4.  Make a prediction for a set of datapoints specified in a csv file defined using the input_path argument.
*Note: Inputs not used (smi1, smi2, molfrac1, T) will be ignored. The csv file should consist of four columns in the following order: SMILES 1, SMILES 2, Mole Fraction, and Temperature. Columns should have headers.

```
# Usage:
# out = [viscosity (cp), mole fraction, dataframe]
# dataframe contains a pandas dataframe with predictions and reliability values
# added in columns to the end of the csv input file.

from mixprop.visc_pred_wrapper import visc_pred_read_csv
import matplotlib.pyplot as plt

out = visc_pred_read_csv(args)
out[-1]
```


