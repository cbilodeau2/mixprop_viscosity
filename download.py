import zenodo_get as zget
from zipfile import ZipFile

zget.zenodo_get(["-r 8042966"])

with ZipFile("pretrained_models.zip","r") as zObject:
    
    zObject.extractall(path=".")
