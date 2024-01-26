# Part-III-AC-Susceptibility-Noise-Calculator
A repository for my Part III Masters Project, on predicting noise in AC susceptibility measurements of nonlinear materials based on finite-element field analysis. This work was done as part of the Quantum Materials Group, Maxwell Centre, Cavendish Laboratory, University of Cambridge.

The 'code/' folder contains the source code, while the 'dist/' folder contains the necessary files for the Windows distribution.

## How to use
**N.B. This is a work-in-progress, there are no valid distributions yet! This section serves as a postmarker for the _intended_ structure of future distributions.**

**<u>Windows</u>.** The 'dist/' folder contains two items: 'suscep_calc.exe', and a 'data/' folder. Download & copy both of these items into the same folder on your computer (they have to be placed in the same location!). You can then run 'suscep_calc.exe' directly with no prerequisites.

**<u>Cross-Platform</u>.** Alternatively, you can run the program as a Python script. Download & copy all of the contents of the 'code/' folder, making sure to preserve the file structure in your install location; you can run the program from 'main.pyw'. Note that you will need the following prerequisites:

- Python installed on your computer, version at least 3.0
- The following Python libraries installed:
	- `numpy`
	- `matplotlib`
	- `pandas`
	- `pint`

## Acknowledgements
This work was written by Darren Wayne Lim, under the joint supervision of Nicholas Popiel and Jiasheng Chen.

Copyrighted (c) 2024 by Darren Wayne Lim under the MIT License.