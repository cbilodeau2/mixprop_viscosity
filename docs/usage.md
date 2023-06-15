## 1. Download Models:

To use mixprop in a project, first download the pretrained models from Zenodo:

```
from mixprop.visc_pred_wrapper import download_models
download_models()
```
Files will be downloaded into your current directory.

## 2. Calculate Predictions:

There are four ways to interact with mixprop.

### 2.1 Make a prediction for a single datapoint.

```
# Usage:
# out = [viscosity (cp), reliability (bool)]

out = visc_pred_single(args)
print('Viscosity = {} cP'.format(out[0]))
print('Reliability = {}'.format(out[1]))
```
