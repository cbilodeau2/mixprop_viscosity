## 1. Download Models:

To use mixprop in a project, first download the pretrained models from Zenodo:

```
from mixprop.visc_pred_wrapper import download_models
download_models()
```
Files will be downloaded into your current directory.

## 2. Calculate Predictions:

There are four types of inputs that you can provide to mixprop:

### 2.1. Make a prediction for a single datapoint.

```
# Usage:
# out = [viscosity (cp), reliability (bool)]

from mixprop.visc_pred_wrapper import visc_pred_single
import matplotlib.pyplot as plt

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


from mixprop.visc_pred_wrapper import visc_pred_T_curve
import matplotlib.pyplot as plt

out = visc_pred_molfrac1_curve(args)

plt.figure(figsize=(3,3),dpi=100)
plt.plot(out[1],out[0],marker='o')
plt.xlabel('Mole Fraction')
plt.ylabel('Viscosity (cP)')
plt.show()
```
