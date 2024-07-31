# Part-III-AC-Susceptibility-Noise-Calculator
A repository for my Part III Masters Project, on predicting noise in AC susceptibility measurements of nonlinear materials based on finite-element field analysis. This work was done as part of the Quantum Materials Group, Maxwell Centre, Cavendish Laboratory, University of Cambridge.

The 'code/' folder contains the source code, while the 'dist/' folder contains the necessary files for the Windows distribution.

## How to use
**<ins>Windows</ins>.** Download the 'dist/AC Susceptibility Noise Calculator' folder on your computer, and save it anywhere you like. You can then run the 'main.exe' file inside the folder directly with no prerequisites.

**<ins>Cross-Platform</ins>.** Alternatively, you can run the program as a Python script. Download & copy all of the contents of the 'code/' folder, making sure to preserve the file structure in your install location; you may rename the 'code/' root folder itself, but not any of the internal folders. You can now run the program from 'main.pyw'. Note that you will need the following prerequisites:

- Python installed on your computer, version at least 3.5
- The following Python libraries installed:
	- `numpy`
	- `scipy`
	- `matplotlib`
	- `pandas`
	- `pint`

## Changelog

#### v0.0.2
Added saving/loading features.

#### v0.0.1
First prototype version! Heavily limited functionalities (e.g. system constrained to be cylindrically-symmetric only), a very clunky UI, and results not rigorously proven yet; intended for demonstration purposes only.

## Acknowledgements
This work was written by Darren Wayne Lim, under the joint supervision of Nicholas Popiel and Jiasheng Chen.

Copyrighted (c) 2024 by Darren Wayne Lim under the MIT License.