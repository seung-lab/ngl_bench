# Neuroglancer Benchmark for Automated Proofreading

## 🧠 Overview

The pipeline to obtain full connectomes (brain wirings) is steadily being fully automated; images obtained by electron microscopy can be processed by segmentation models to then build comprehensive 3D models of individual neurons. However, despite their superhuman precision, model outputs of the reconstructed neurons bear errors. 

Currently, a team of human proofreaders are manually finding these errors on the connectome of a femla Drosophila and correcting them through a Web Interface called **Neuroglancer**, which allows for both 3D and 2D cross-section visualization of neuron data.

This is **unscalable**. Proofreaders must tediously analyze the local structure and global context of neurons to assess for errors (typically an accidental merging of neurons or separation of an individual neuron). Even for smaller connectomes, such as that of the female Drosophila, this proves to be a monumental task.

We need **Agents** capable of making human-level observations as well as decisions and applying them through the Web interface onto the neurons to help our team. This is no easy task - proofreading aside, the Neuroglancer environment is a challenge to successfully understand and utilize due to its many dynamic visual inputs. While the overall goal is fully automated proofreading, there are several intermediate challenges that agentic approachs must address such as efficiently navigating through neurons, finding errors, and finding synapses...

## ❔ Understanding the Setup

- **[Flywire Environment Tutorial](https://ngl.flywire.ai/)**: Provides access to neurons in a Neuroglancer-like environment, including a proofreading & navigation tutorial. This gives access to the neuron reconstruction of the female fly brain.

## Example Videos  

### 1. Human Proofreader in Action  
Example of a human proofreader making a sequence of actions. He detects an **abnormal cut**, explores the nearby environment and corrects the error.  

[![Proofreading Video](example_videos/gifs/video_1.gif)](example_videos/gifs/video_1.gif)  

### 2. Model Clicking on the Highest Z Position  
Example of a trained model clicks on the **highest Z position** (blue axis) of a neuron within its field of view. The action space is limited to clicking only. Future improvements could incorporate **zooming out and changing orientation** for faster navigation. Manipulating a 3D environment is a difficult task and is one of the main challenges in automated proofreading.

[![Highest Z Clicker](example_videos/gifs/video_2.gif)](example_videos/gifs/video_2.gif)  

### 3. Programmatic Use of Neuroglancer  
Existing code for **Neuroglancer integration with Python**, showing how the environment can be used in **reinforcement learning (RL)** setups to return images, states, and execute direct actions. The code  was built for fast querying by writing direct Javascript commands with Selenium.

[![Neuroglancer Environment](example_videos/gifs/video_3.gif)](example_videos/gifs/video_3.gif)  
