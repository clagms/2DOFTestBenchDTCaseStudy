# Setup of interactive notebook
This presentation demonstraties how to setup an interactive python notebook `.ipynb` as our interactive computing environment. Follow the steps below supported by an image;

1. Create a new file and name it `script_beam2d.ipynb` (shown as <span class="red">**A**</span>).
2. Select "Select Kernel" to choose the virtual enviornment (venv) to run (shown as <span class="red">**B**</span>)
3. Select the venv which is installed in the directory (Shown as <span class="red">**C**</span>).
    1. You may initially need to select `Install/Enable suggested exttensions` in the selection window <span class="red">**C**</span> shown in the figure.
    2. You may initially need to select `Python Enviornments...` in the selection window <span class="red">**C**</span> shown in the figure.

<img src="Images/tutorial_setup_notebook.svg" width="70%">


The notebook is now fully setup with the created venv selected as our Kernel. We now have the option to add code cells, and Markdown cells.

<img src="Images/tutorial_notebook_navigation.svg" width="70%">

## Navigation in the the notebook

We can now add a Markdown cell and type `# Packages` according to <span class="red">**A**</span>. To render the Markdown cell press <span class="red">**B**</span>. Notice that the added Markdown cell is a heading, which in turn shows up in the Outline.

<img src="Images/tutorial_notebook_navigation_continued.svg" width="70%">

Next we can add a Code cell containing Python code. Type the following according to <span class="red">**A**</span> and execute the cell in <span class="red">**B**</span>. \
Located at the very top of the window, we have additional navigation and execution tools. From here, we can add a `Code` cell, a `Markdown` cell and run all the cells by pressing `Run All`. To clear the variable space and restart the venv, press `Restart`. Inside `Jupyter Variable` is our variable space, where we can inspect all our stored variables.

<img src="Images/tutorial_notebook_navigation_continued2.svg" width="70%">

## Hotkeys

Working in a Jupyter Notebook using the default hotkeys makes coding substantially faster and more enjoyable and is therefor highly recommended to get familiar with. This tutorial won't however cover the this topic, but can be found [here](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).